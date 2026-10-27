import struct

import pytest

from tools import ebootstr, prx

R_MIPS_32 = 2


def elf(rodata, data, pointers):
    """Tiny PRX with one LOAD segment (.rodata then .data), relocations and section headers.

    pointers: rodata offsets stored as R_MIPS_32 words at the start of .data."""
    table = b"".join(struct.pack("<I", o) for o in pointers)
    data = table + data
    seg = rodata + data
    rel = b"".join(struct.pack("<II", 4 * i + len(rodata), R_MIPS_32) for i in range(len(pointers)))
    names = b"\0.rodata\0.data\0.shstrtab\0"
    phoff, phnum, shnum = 52, 2, 4
    seg_off = phoff + 32 * phnum
    rel_off = seg_off + len(seg)
    str_off = rel_off + len(rel)
    shoff = str_off + len(names)
    ph = [(1, seg_off, 0, 0, len(seg), len(seg), 7, 16), (0x700000A0, rel_off, 0, 0, len(rel), 0, 0, 16)]
    sh = [(0,) * 10,
          (1, 1, 2, 0, seg_off, len(rodata), 0, 0, 4, 0),
          (9, 1, 3, len(rodata), seg_off + len(rodata), len(data), 0, 0, 4, 0),
          (15, 3, 0, 0, str_off, len(names), 0, 0, 1, 0)]
    hdr = b"\x7fELF" + bytes(12) + struct.pack("<HHIIIIIHHHHHH", 0xFFA0, 8, 1, 0, phoff, shoff, 0,
                                               52, 32, phnum, 40, shnum, 3)
    return (hdr + b"".join(struct.pack("<8I", *p) for p in ph) + seg + rel + names
            + b"".join(struct.pack("<10I", *s) for s in sh))


def strings(*items):
    """NUL-separated cp932 pool starting with padding; returns (pool, offsets)."""
    pool, offs = bytearray(4), []
    for s in items:
        offs.append(len(pool))
        pool += s.encode("cp932") + b"\0"
    pool += bytes(-len(pool) % 4)
    return bytes(pool), offs


def sample():
    pool, offs = strings("敵を倒そう！", "ﾃｽﾄ", "OK", "%sは新しいスキルを覚えた！@n", "@c<06>ギャラリー@c<00>")
    return elf(pool, b"", offs + [offs[0]]), offs


def test_sections_are_read_from_the_header():
    data, _ = sample()
    names = [s.name for s in prx.sections(data)]
    assert names == ["", ".rodata", ".data", ".shstrtab"]


def test_catalog_keeps_clean_japanese_strings_with_their_pointers():
    data, offs = sample()
    cat = ebootstr.catalog(data)
    assert [(t.va, t.text) for t in cat] == [
        (offs[0], "敵を倒そう！"), (offs[3], "%sは新しいスキルを覚えた！@n"), (offs[4], "@c<06>ギャラリー@c<00>")]
    assert len(cat[0].refs) == 2  # two pointers to the same string


def test_template_has_ids_and_no_source_text():
    data, offs = sample()
    t = ebootstr.template(data)
    assert [e["id"] for e in t["entries"]] == [f"eboot:{o:#x}" for o in (offs[0], offs[3], offs[4])]
    assert all(e["state"] == "untranslated" and e["ko"] == "" for e in t["entries"])
    assert "敵" not in repr(t)


@pytest.mark.parametrize("src,ko,ok", [
    ("%sは新しいスキルを覚えた！@n", "%s은(는) 새 스킬을 익혔다!@n", True),
    ("%sは新しいスキルを覚えた！@n", "새 스킬을 익혔다!@n", False),        # format specifier lost
    ("@c<06>ギャラリー@c<00>", "@c<06>갤러리@c<00>", True),
    ("@c<06>ギャラリー@c<00>", "갤러리", False),                           # colour codes lost
    ("∈：決定", "∈: 결정", True),
    ("∈：決定", "○: 결정", False),                                         # button glyph lost
    ("決定", "결정똠", False),                                             # not encodable
])
def test_check_protects_formats_codes_and_button_glyphs(src, ko, ok):
    assert (ebootstr.check(src, ko) == []) is ok


def test_line_widths_count_full_width_as_two_and_skip_codes():
    assert ebootstr.line_widths("@c<06>ギャラリー@c<00>") == [10]
    assert ebootstr.line_widths("ＨＰ回復@n%s") == [8, 2]
    assert ebootstr.line_widths("갤러리 OK") == [9]


def test_wider_lines_are_reported():
    assert ebootstr.wider_lines("スキル取得", "스킬 획득") == []
    assert ebootstr.wider_lines("決定", "결정하기") == [(1, 8, 4)]
