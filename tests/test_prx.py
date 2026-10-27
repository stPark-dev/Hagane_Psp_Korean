import struct

import pytest

from tools import prx

R_MIPS_32, R_MIPS_HI16, R_MIPS_LO16 = 2, 5, 6


def elf(seg0, seg1_data, seg1_mem, relocs, gap=0x100):
    """Tiny PRX: seg0 at vaddr 0, seg1 right after it, zero gap, then relocations."""
    phoff, phnum = 52, 3
    off0 = phoff + 32 * phnum
    v1 = len(seg0)
    off1 = off0 + len(seg0)
    rel = b"".join(struct.pack("<II", o, t | ob << 8 | ab << 16) for o, t, ob, ab in relocs)
    offr = off1 + len(seg1_data) + gap
    ph = [(1, off0, 0, 0, len(seg0), len(seg0), 7, 16),
          (1, off1, v1, 0, len(seg1_data), seg1_mem, 6, 16),
          (0x700000A0, offr, 0, 0, len(rel), 0, 0, 16)]
    hdr = b"\x7fELF" + bytes(12) + struct.pack("<HHIIIIIHHHHHH", 0xFFA0, 8, 1, 0, phoff, 0, 0,
                                               52, 32, phnum, 40, 0, 0)
    body = hdr + b"".join(struct.pack("<8I", *p) for p in ph)
    return body + seg0 + seg1_data + bytes(gap) + rel


def sample():
    # seg0: code word (lui/addiu pair) + strings; seg1: pointer table
    seg0 = struct.pack("<II", 0x3C040000, 0x24840010) + bytes(8) + b"AB\0\0CDE\0" + b"F\0\0\0"
    table = struct.pack("<III", 0x10, 0x14, 0x14)
    relocs = [(0, R_MIPS_HI16, 0, 0), (4, R_MIPS_LO16, 0, 0),
              (0, R_MIPS_32, 1, 0), (4, R_MIPS_32, 1, 0), (8, R_MIPS_32, 1, 0)]
    return elf(seg0, table, len(table) + 8, relocs)


def test_parse_reads_segments_and_relocations():
    p = prx.parse(sample())
    assert [s.vaddr for s in p.loads] == [0, 0x1C]
    assert len(p.relocs) == 5
    assert p.va_to_offset(0x1C) == p.loads[1].offset


def test_pointer_refs_and_hilo_targets():
    data = sample()
    p = prx.parse(data)
    refs = prx.pointer_refs(p, data)
    assert refs[0x10] == [0x1C]
    assert refs[0x14] == [0x20, 0x24]
    assert prx.hilo_targets(p, data) == {0x10}


def test_move_strings_appends_after_bss_and_repoints():
    data = sample()
    out, moved = prx.move_strings(data, {0x14: b"KOREAN"})
    p = prx.parse(out)
    new = moved[0x14]
    assert new >= 0x1C + 12 + 8  # after seg1 memsz (data + bss)
    assert prx.pointer_refs(p, out)[new] == [0x20, 0x24]
    off = p.va_to_offset(new)
    assert out[off:off + 7] == b"KOREAN\0"
    assert len(out) == len(data)  # placed in the zero gap, file does not grow
    assert out[p.va_to_offset(0x14):p.va_to_offset(0x14) + 4] == b"CDE\0"  # original kept
    assert p.loads[1].filesz == p.loads[1].memsz


def test_move_refuses_hilo_referenced_string():
    with pytest.raises(ValueError, match="HI16"):
        prx.move_strings(sample(), {0x10: b"X"})


def test_move_refuses_unreferenced_address():
    with pytest.raises(ValueError, match="no pointer"):
        prx.move_strings(sample(), {0x18: b"X"})


def test_move_refuses_when_gap_is_too_small():
    with pytest.raises(ValueError, match="space"):
        prx.move_strings(sample(), {0x14: b"K" * 0x200})


def test_unchanged_when_nothing_moved():
    data = sample()
    assert prx.move_strings(data, {})[0] == data
