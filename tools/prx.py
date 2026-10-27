"""PSP PRX (decrypted EBOOT) program headers, relocations and sections (read only).

Relocation entries (program header type 0x700000A0) are 8 bytes:
offset (relative to load segment `ofsbase`) and info = type | ofsbase<<8 |
addrbase<<16. An R_MIPS_32 word holds an address relative to segment
`addrbase`.

move_strings never overwrites an original string: translated strings go to a
new area right after the last load segment's bss (in the zero gap that the
decrypted file already has) and every R_MIPS_32 pointer to the old address
is repointed. Strings reached through HI16/LO16 code pairs are refused.
(Branch poc/eboot-strings only until verified on a real PSP, D7.)
"""
import struct
from dataclasses import dataclass, replace

PT_LOAD = 1
PT_PRX_RELOC = 0x700000A0
R_MIPS_32, R_MIPS_HI16, R_MIPS_LO16 = 2, 5, 6


@dataclass(frozen=True)
class Segment:
    index: int
    type: int
    offset: int
    vaddr: int
    paddr: int
    filesz: int
    memsz: int
    flags: int
    align: int


@dataclass(frozen=True)
class Reloc:
    offset: int
    type: int
    ofsbase: int
    addrbase: int


@dataclass(frozen=True)
class Prx:
    phoff: int
    segments: tuple
    relocs: tuple
    shoff: int
    shnum: int
    shentsize: int

    @property
    def loads(self):
        return [s for s in self.segments if s.type == PT_LOAD]

    def va_to_offset(self, va):
        for s in self.loads:
            if s.vaddr <= va < s.vaddr + max(s.filesz, s.memsz):
                return s.offset + va - s.vaddr
        raise ValueError(f"address {va:#x} is outside the load segments")

    def reloc_va(self, r):
        return self.loads[r.ofsbase].vaddr + r.offset


def parse(data):
    phoff, = struct.unpack_from("<I", data, 0x1C)
    shoff, = struct.unpack_from("<I", data, 0x20)
    phnum, shentsize, shnum = struct.unpack_from("<H", data, 0x2C)[0], *struct.unpack_from("<HH", data, 0x2E)
    segments = tuple(Segment(i, *struct.unpack_from("<8I", data, phoff + 32 * i)) for i in range(phnum))
    relocs = []
    for s in segments:
        if s.type == PT_PRX_RELOC:
            for o, info in struct.iter_unpack("<II", data[s.offset:s.offset + s.filesz]):
                relocs.append(Reloc(o, info & 0xFF, (info >> 8) & 0xFF, (info >> 16) & 0xFF))
    return Prx(phoff, segments, tuple(relocs), shoff, shnum, shentsize)


def _word(p, data, va):
    return struct.unpack_from("<I", data, p.va_to_offset(va))[0]


def pointer_refs(p, data):
    """{target address: [addresses of R_MIPS_32 words pointing at it]}"""
    refs = {}
    for r in p.relocs:
        if r.type == R_MIPS_32:
            va = p.reloc_va(r)
            refs.setdefault(_word(p, data, va) + p.loads[r.addrbase].vaddr, []).append(va)
    return refs


def hilo_targets(p, data):
    """Addresses built by HI16/LO16 pairs; a LO16 without a new HI16 reuses the last ones."""
    out, pending, last = set(), [], []
    for r in p.relocs:
        if r.type == R_MIPS_HI16:
            pending.append(_word(p, data, p.reloc_va(r)) & 0xFFFF)
        elif r.type == R_MIPS_LO16:
            last = pending or last
            pending = []
            lo = _word(p, data, p.reloc_va(r)) & 0xFFFF
            lo -= (lo & 0x8000) << 1
            out.update((hi << 16) + lo + p.loads[r.addrbase].vaddr for hi in last)
    return out


@dataclass(frozen=True)
class Section:
    name: str
    type: int
    addr: int
    offset: int
    size: int


def sections(data):
    shoff, = struct.unpack_from("<I", data, 0x20)
    shentsize, shnum, shstrndx = struct.unpack_from("<HHH", data, 0x2E)
    raw = [struct.unpack_from("<IIIIII", data, shoff + i * shentsize) for i in range(shnum)]
    if not raw:
        return []
    names = raw[shstrndx][4]

    def name(o):
        return data[names + o:data.index(b"\0", names + o)].decode("ascii")
    return [Section(name(n), t, a, o, s) for n, t, _, a, o, s in raw]


def _file_limit(p, data, start):
    """First file offset at or after `start` used by another structure."""
    ends = [s.offset for s in p.segments if s.offset >= start and s.filesz]
    if p.shnum:
        ends.append(p.shoff)
        for i in range(p.shnum):
            stype, off, size = struct.unpack_from("<4xI8xII", data, p.shoff + i * p.shentsize)
            if stype != 8 and size and off >= start:  # 8 = SHT_NOBITS
                ends.append(off)
    return min(ends, default=len(data))


def move_strings(data, strings):
    """Return (new data, {old address: new address}). strings: {old address: bytes without NUL}."""
    if not strings:
        return data, {}
    p = parse(data)
    refs = pointer_refs(p, data)
    hilo = hilo_targets(p, data)
    for va in strings:
        if va in hilo:
            raise ValueError(f"{va:#x} is reached through HI16/LO16 code; not movable")
        if va not in refs:
            raise ValueError(f"{va:#x} has no pointer to it")
    seg = p.loads[-1]
    start = (seg.vaddr + seg.memsz + 15) & ~15
    blob, moved = bytearray(), {}
    for va, text in strings.items():
        moved[va] = start + len(blob)
        blob += text + b"\0"
        blob += bytes(-len(blob) % 4)
    end_va = start + len(blob)
    zero_from = seg.offset + seg.filesz
    end_off = seg.offset + end_va - seg.vaddr
    if end_off > _file_limit(p, data, zero_from) or any(data[zero_from:end_off]):
        raise ValueError(f"not enough zero space after segment {seg.index} for {len(blob)} bytes")
    out = bytearray(data)
    out[seg.offset + start - seg.vaddr:end_off] = blob
    grown = replace(seg, filesz=end_va - seg.vaddr, memsz=end_va - seg.vaddr)
    struct.pack_into("<8I", out, p.phoff + 32 * seg.index, *[getattr(grown, f) for f in (
        "type", "offset", "vaddr", "paddr", "filesz", "memsz", "flags", "align")])
    for r in p.relocs:
        if r.type != R_MIPS_32:
            continue
        va = p.reloc_va(r)
        base = p.loads[r.addrbase].vaddr
        target = _word(p, data, va) + base
        if target in moved:
            struct.pack_into("<I", out, p.va_to_offset(va), moved[target] - base)
    return bytes(out), moved


def overwrite(data, strings):
    """Return data with strings replaced in place: {address of a string start: new bytes without NUL}.

    The new text must fit the old string's bytes; the rest is filled with NUL so
    the terminator and everything after the old string stay as they were. Used
    for strings that code reaches through HI16/LO16 pairs and cannot move."""
    p = parse(data)
    out = bytearray(data)
    for va, new in strings.items():
        off = p.va_to_offset(va)
        if off == 0 or data[off - 1] != 0:
            raise ValueError(f"{va:#x} is not the start of a string")
        old_len = data.index(b"\0", off) - off
        if len(new) > old_len or b"\0" in new:
            raise ValueError(f"{va:#x}: new text is longer than the {old_len} bytes available")
        out[off:off + old_len] = new + bytes(old_len - len(new))
    return bytes(out)
