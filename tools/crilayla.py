"""CRILAYLA compression (the inverse of cpk.decompress_crilayla), so replaced CPK files can stay compressed.

Layout: b"CRILAYLA", u32 usize (bytes after the 0x100 prefix), u32 csize (bitstream bytes, a multiple of 4, zero-padded at the front), the bitstream, then the
first 0x100 bytes of the data verbatim. The bitstream is read MSB-first from its last byte
backwards and fills the output from the end: 0 + 8 bits = literal; 1 + 13 bits offset + length
levels (2, 3, 5, 8, then 8... bits) = copy from offset + 3 bytes above.

The match finder runs under numba when it is installed (about a hundred times faster); without it
the same code runs as plain Python, which is only practical for small inputs.
"""
import struct

import numpy as np

try:
    from numba import njit
except ImportError:  # pragma: no cover - plain Python fallback
    def njit(*a, **k):
        return (lambda f: f) if not a or not callable(a[0]) else a[0]

PREFIX = 0x100
MAX_DIST = 8194          # offset field is 13 bits, distance = offset + 3
MAX_CHAIN = 128
HASH_BITS = 16


@njit(cache=True)
def _hash(data, q):
    h = (np.int64(data[q]) << 16) | (np.int64(data[q - 1]) << 8) | np.int64(data[q - 2])
    return ((h * 2654435761) & 0xFFFFFFFF) >> (32 - HASH_BITS)


@njit(cache=True)
def _put(buf, nbits, value, width):
    for k in range(width - 1, -1, -1):
        if (value >> k) & 1:
            buf[nbits >> 3] |= np.uint8(0x80 >> (nbits & 7))
        nbits += 1
    return nbits


@njit(cache=True)
def _encode(data):
    """Bitstream (in reading order) and its length in bits."""
    n = data.shape[0]
    buf = np.zeros((n - PREFIX) * 9 // 8 + 64, np.uint8)
    head = np.full(1 << HASH_BITS, -1, np.int64)
    prev = np.full(n, -1, np.int64)
    nbits = 0
    p = n - 1
    while p >= PREFIX:
        best_len = 0
        best_r = 0
        maxlen = p - PREFIX + 1
        if maxlen >= 3:
            r = head[_hash(data, p)]
            chain = 0
            while r != -1 and r - p <= MAX_DIST and chain < MAX_CHAIN:
                if r - p >= 3:
                    l = 0
                    while l < maxlen and data[p - l] == data[r - l]:
                        l += 1
                    if l > best_len:
                        best_len = l
                        best_r = r
                        if l == maxlen:
                            break
                r = prev[r]
                chain += 1
        step = 1
        if best_len >= 3:
            nbits = _put(buf, nbits, 1, 1)
            nbits = _put(buf, nbits, best_r - p - 3, 13)
            v = best_len - 3
            done = False
            for w in (2, 3, 5, 8):
                m = (1 << w) - 1
                if v < m:
                    nbits = _put(buf, nbits, v, w)
                    done = True
                    break
                nbits = _put(buf, nbits, m, w)
                v -= m
            if not done:
                while True:
                    if v < 255:
                        nbits = _put(buf, nbits, v, 8)
                        break
                    nbits = _put(buf, nbits, 255, 8)
                    v -= 255
            step = best_len
        else:
            nbits = _put(buf, nbits, 0, 1)
            nbits = _put(buf, nbits, np.int64(data[p]), 8)
        for q in range(p, p - step, -1):
            if q - 2 >= 0:
                h = _hash(data, q)
                prev[q] = head[h]
                head[h] = q
        if buf.shape[0] - (nbits >> 3) < 64:
            grown = np.zeros(buf.shape[0] * 2, np.uint8)
            grown[:buf.shape[0]] = buf
            buf = grown
        p -= step
    return buf, nbits


@njit(cache=True)
def _decode(body, prefix, usize):
    out = np.zeros(PREFIX + usize, np.uint8)
    out[:PREFIX] = prefix
    pos = body.shape[0] - 1
    pool = 0
    left = 0
    end = PREFIX + usize - 1
    done = 0
    while done < usize:
        # one bit
        if left == 0:
            pool = np.int64(body[pos]); pos -= 1; left = 8
        left -= 1
        if (pool >> left) & 1:
            v = 0
            for _ in range(13):
                if left == 0:
                    pool = np.int64(body[pos]); pos -= 1; left = 8
                left -= 1
                v = (v << 1) | ((pool >> left) & 1)
            ref = end - done + v + 3
            length = 3
            more = True
            for w in (2, 3, 5, 8):
                lv = 0
                for _ in range(w):
                    if left == 0:
                        pool = np.int64(body[pos]); pos -= 1; left = 8
                    left -= 1
                    lv = (lv << 1) | ((pool >> left) & 1)
                length += lv
                if lv != (1 << w) - 1:
                    more = False
                    break
            while more:
                lv = 0
                for _ in range(8):
                    if left == 0:
                        pool = np.int64(body[pos]); pos -= 1; left = 8
                    left -= 1
                    lv = (lv << 1) | ((pool >> left) & 1)
                length += lv
                more = lv == 0xFF
            for _ in range(length):
                out[end - done] = out[ref]
                ref -= 1
                done += 1
        else:
            v = 0
            for _ in range(8):
                if left == 0:
                    pool = np.int64(body[pos]); pos -= 1; left = 8
                left -= 1
                v = (v << 1) | ((pool >> left) & 1)
            out[end - done] = v
            done += 1
    return out


def compress(data):
    """CRILAYLA stream for data (len > 0x100)."""
    if len(data) <= PREFIX:
        raise ValueError("CRILAYLA needs more than 0x100 bytes")
    arr = np.frombuffer(bytes(data), np.uint8)
    buf, nbits = _encode(arr)
    stream = buf[:-(-nbits // 8)][::-1].tobytes()
    pad = -len(stream) % 4
    body = bytes(pad) + stream
    return b"CRILAYLA" + struct.pack("<II", len(data) - PREFIX, len(body)) + body + bytes(data[:PREFIX])


def decompress(src):
    """Fast equivalent of cpk.decompress_crilayla (used to verify compress output)."""
    if src[:8] != b"CRILAYLA":
        raise ValueError("not a CRILAYLA stream")
    usize, csize = struct.unpack_from("<II", src, 8)
    body = np.frombuffer(src, np.uint8, csize, 0x10)
    prefix = np.frombuffer(src, np.uint8, PREFIX, 0x10 + csize)
    return _decode(body, prefix, usize).tobytes()
