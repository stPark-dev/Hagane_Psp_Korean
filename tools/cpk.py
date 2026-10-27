"""CRI CPK archive reader: @UTF tables, TOC/ITOC listings, CRILAYLA decompression."""
import struct
from dataclasses import dataclass
from pathlib import Path

_FIXED = {0: ">B", 1: ">b", 2: ">H", 3: ">h", 4: ">I", 5: ">i",
          6: ">Q", 7: ">q", 8: ">f", 9: ">d"}
STORAGE_ZERO, STORAGE_CONST, STORAGE_ROW = 0x10, 0x30, 0x50
TYPE_STRING, TYPE_DATA = 0xA, 0xB


def parse_utf(buf):
    """Parse an @UTF table. Returns (table_name, [row dicts]).
    Data-typed cells are returned as bytes."""
    name, rows, _ = parse_utf_positions(buf)
    return name, rows


def parse_utf_positions(buf):
    """Like parse_utf, plus per-row {column: (offset in buf, struct fmt)} for
    fixed-width per-row cells, so values can be patched in place."""
    if buf[:4] != b"@UTF":
        raise ValueError(f"not an @UTF table: {bytes(buf[:4])!r}")
    size, = struct.unpack_from(">I", buf, 4)
    t = bytes(buf[8:8 + size])
    _, rows_off, str_off, data_off, name_off, ncol, rowlen, nrows = \
        struct.unpack_from(">HHIIIHHI", t, 0)

    def string(o):
        start = str_off + o
        return t[start:t.index(b"\0", start)].decode("cp932")

    def read(p, ty):
        if ty in _FIXED:
            return struct.unpack_from(_FIXED[ty], t, p)[0], struct.calcsize(_FIXED[ty])
        if ty == TYPE_STRING:
            return string(struct.unpack_from(">I", t, p)[0]), 4
        if ty == TYPE_DATA:
            o, n = struct.unpack_from(">II", t, p)
            return t[data_off + o:data_off + o + n], 8
        raise ValueError(f"unknown @UTF column type {ty:#x}")

    cols = []
    p = 24
    for _ in range(ncol):
        flags = t[p]
        cname = string(struct.unpack_from(">I", t, p + 1)[0])
        p += 5
        storage, ty = flags & 0xF0, flags & 0x0F
        const = None
        if storage == STORAGE_CONST:
            const, n = read(p, ty)
            p += n
        elif storage not in (STORAGE_ZERO, STORAGE_ROW):
            raise ValueError(f"unknown @UTF storage {storage:#x} in column {cname}")
        cols.append((cname, storage, ty, const))

    rows = []
    positions = []
    for r in range(nrows):
        p = rows_off + r * rowlen
        row = {}
        pos = {}
        for cname, storage, ty, const in cols:
            if storage == STORAGE_ROW:
                if ty in _FIXED:
                    pos[cname] = (8 + p, _FIXED[ty])
                row[cname], n = read(p, ty)
                p += n
            else:
                row[cname] = const
        rows.append(row)
        positions.append(pos)
    return string(name_off), rows, positions


def decompress_crilayla(src):
    """Decompress a CRILAYLA stream (header + backward LZ body + 0x100 raw prefix)."""
    if src[:8] != b"CRILAYLA":
        raise ValueError("not a CRILAYLA stream")
    usize, comp_size = struct.unpack_from("<II", src, 8)
    out = bytearray(0x100 + usize)
    out[:0x100] = src[0x10 + comp_size:0x10 + comp_size + 0x100]
    pos = 0x10 + comp_size - 1
    pool = 0
    left = 0

    def bits(n):
        nonlocal pos, pool, left
        v = 0
        while n:
            if left == 0:
                pool = src[pos]
                pos -= 1
                left = 8
            take = min(left, n)
            v = (v << take) | ((pool >> (left - take)) & ((1 << take) - 1))
            left -= take
            n -= take
        return v

    end = 0x100 + usize - 1
    done = 0
    while done < usize:
        if bits(1):
            ref = end - done + bits(13) + 3
            length = 3
            for width in (2, 3, 5, 8):
                level = bits(width)
                length += level
                if level != (1 << width) - 1:
                    break
            else:
                while True:
                    level = bits(8)
                    length += level
                    if level != 0xFF:
                        break
            for _ in range(length):
                out[end - done] = out[ref]
                ref -= 1
                done += 1
        else:
            out[end - done] = bits(8)
            done += 1
    return bytes(out)


@dataclass(frozen=True)
class Entry:
    index: int
    id: int
    path: str
    offset: int        # absolute offset in the .cpk
    size: int          # stored size
    extract_size: int

    @property
    def compressed(self):
        return self.size != self.extract_size


class CpkArchive:
    def __init__(self, path):
        self.path = Path(path)
        with open(self.path, "rb") as f:
            head = f.read(0x800)
            if head[:4] != b"CPK ":
                raise ValueError(f"{path}: not a CPK archive")
            _, rows = parse_utf(head[0x10:])
            self.header = rows[0]
            if self.header.get("TocOffset"):
                self.entries = self._read_toc(f)
            elif self.header.get("ItocOffset"):
                self.entries = self._read_itoc(f)
            else:
                raise ValueError(f"{path}: no TOC or ITOC")

    def _chunk(self, f, offset, size, magic):
        f.seek(offset)
        buf = f.read(size)
        if buf[:4] != magic:
            raise ValueError(f"{self.path}: expected {magic!r} at {offset:#x}")
        return buf[0x10:]

    def _read_toc(self, f):
        h = self.header
        _, rows = parse_utf(self._chunk(f, h["TocOffset"], h["TocSize"], b"TOC "))
        base = min(h["TocOffset"], h["ContentOffset"])
        out = []
        for i, r in enumerate(rows):
            path = f"{r['DirName']}/{r['FileName']}" if r["DirName"] else r["FileName"]
            out.append(Entry(i, r["ID"], path, base + r["FileOffset"],
                             r["FileSize"], r["ExtractSize"]))
        return out

    def _read_itoc(self, f):
        h = self.header
        _, top = parse_utf(self._chunk(f, h["ItocOffset"], h["ItocSize"], b"ITOC"))
        sizes = {}
        for key in ("DataL", "DataH"):
            blob = top[0][key]
            if blob:
                for r in parse_utf(blob)[1]:
                    sizes[r["ID"]] = (r["FileSize"], r["ExtractSize"])
        if len(sizes) != h["Files"]:
            raise ValueError(f"{self.path}: ITOC lists {len(sizes)} files, header {h['Files']}")
        align = h["Align"]
        offset = h["ContentOffset"]
        out = []
        for i, fid in enumerate(sorted(sizes)):
            size, extract = sizes[fid]
            out.append(Entry(i, fid, f"{fid:05d}", offset, size, extract))
            offset += -(-size // align) * align
        return out

    def by_path(self):
        return {e.path: e for e in self.entries}

    def read_raw(self, entry):
        with open(self.path, "rb") as f:
            f.seek(entry.offset)
            return f.read(entry.size)

    def read(self, entry):
        data = self.read_raw(entry)
        if entry.compressed:
            data = decompress_crilayla(data)
            if len(data) != entry.extract_size:
                raise ValueError(f"{entry.path}: expanded to {len(data)}, expected {entry.extract_size}")
        return data


def _align(n, a):
    return -(-n // a) * a


def _patch(buf, pos, column, value):
    if column not in pos:
        raise ValueError(f"column {column} is not a per-row fixed-width cell")
    off, fmt = pos[column]
    struct.pack_into(fmt, buf, off, value)


def rebuild(src, out, replacements, compress=False):
    """Write a copy of a TOC-based CPK with some files replaced.

    replacements: {entry path: new bytes}; replaced files are stored
    uncompressed, or with compress=True as CRILAYLA when the original was
    compressed, the new data is no larger than the original and the stream
    is smaller (each stream is checked by decompressing it again). Physical file order and alignment are preserved, and the
    TOC/header fields that depend on sizes and offsets are patched in place,
    so an empty replacement set reproduces the source byte for byte."""
    arc = CpkArchive(src)
    h = arc.header
    if not h.get("TocOffset") or h.get("EtocOffset") or h.get("GtocOffset"):
        raise ValueError(f"{src}: only plain TOC archives are supported")
    paths = arc.by_path()
    for p in replacements:
        if p not in paths:
            raise KeyError(p)
    if compress:
        from tools import crilayla  # numba import is slow; only load it when asked
    stored = {}
    for p, data in replacements.items():
        stored[p] = data
        e = paths[p]
        # the game unpacks a compressed file into a buffer sized for the original: a grown file
        # (the Korean FAfont14.fon) hangs the boot when compressed, so it goes in uncompressed
        if compress and e.compressed and len(data) <= e.extract_size and len(data) > crilayla.PREFIX:
            c = crilayla.compress(data)
            if len(c) < len(data):
                if crilayla.decompress(c) != data:
                    raise ValueError(f"{p}: CRILAYLA round trip failed")
                stored[p] = c
    align = h["Align"]
    content_off = h["ContentOffset"]
    toc_off = h["TocOffset"]
    base = min(toc_off, content_off)

    with open(src, "rb") as f:
        head = bytearray(f.read(content_off))
    _, _, hpos = parse_utf_positions(head[0x10:])
    _, _, tpos = parse_utf_positions(head[toc_off + 0x10:])
    hpos = {k: (o + 0x10, fmt) for k, (o, fmt) in hpos[0].items()}
    tpos = [{k: (o + toc_off + 0x10, fmt) for k, (o, fmt) in r.items()} for r in tpos]

    layout = []
    cursor = content_off
    for e in sorted(arc.entries, key=lambda e: e.offset):
        if e.path in replacements:
            size, extract = len(stored[e.path]), len(replacements[e.path])
        else:
            size, extract = e.size, e.extract_size
        offset = _align(cursor, align)
        layout.append((e, offset, size, extract))
        cursor = offset + size
    end = cursor

    for e, offset, size, extract in layout:
        pos = tpos[e.index]
        _patch(head, pos, "FileOffset", offset - base)
        _patch(head, pos, "FileSize", size)
        _patch(head, pos, "ExtractSize", extract)
    total_size = sum(size for _, _, size, _ in layout)
    total_extract = sum(extract for _, _, _, extract in layout)
    _patch(head, hpos, "ContentSize", _align(end - content_off, align))
    _patch(head, hpos, "EnabledDataSize", total_size + total_extract)
    _patch(head, hpos, "EnabledPackedSize", 2 * total_extract)

    with open(src, "rb") as fin, open(out, "wb") as fout:
        fout.write(head)
        written = content_off
        for e, offset, size, _ in layout:
            fout.write(bytes(offset - written))
            if e.path in replacements:
                fout.write(stored[e.path])
            else:
                fin.seek(e.offset)
                fout.write(fin.read(e.size))
            written = offset + size
