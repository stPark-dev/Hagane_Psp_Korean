import struct

import pytest

from tools import ebootstr, kofont, kotext, prx

R_MIPS_32 = 2


def elf(rodata, data, pointers, gap=0):
    """Tiny PRX with one LOAD segment (.rodata then .data), relocations and section headers.

    pointers: rodata offsets stored as R_MIPS_32 words at the start of .data."""
    table = b"".join(struct.pack("<I", o) for o in pointers)
    data = table + data
    seg = rodata + data
    zeros = bytes(gap)  # free space after the segment (the real EBOOT has ~318 KB)
    rel = b"".join(struct.pack("<II", 4 * i + len(rodata), R_MIPS_32) for i in range(len(pointers)))
    names = b"\0.rodata\0.data\0.shstrtab\0"
    phoff, phnum, shnum = 52, 2, 4
    seg_off = phoff + 32 * phnum
    rel_off = seg_off + len(seg) + gap
    str_off = rel_off + len(rel)
    shoff = str_off + len(names)
    ph = [(1, seg_off, 0, 0, len(seg), len(seg), 7, 16), (0x700000A0, rel_off, 0, 0, len(rel), 0, 0, 16)]
    sh = [(0,) * 10,
          (1, 1, 2, 0, seg_off, len(rodata), 0, 0, 4, 0),
          (9, 1, 3, len(rodata), seg_off + len(rodata), len(data), 0, 0, 4, 0),
          (15, 3, 0, 0, str_off, len(names), 0, 0, 1, 0)]
    hdr = b"\x7fELF" + bytes(12) + struct.pack("<HHIIIIIHHHHHH", 0xFFA0, 8, 1, 0, phoff, shoff, 0,
                                               52, 32, phnum, 40, shnum, 3)
    return (hdr + b"".join(struct.pack("<8I", *p) for p in ph) + seg + zeros + rel + names
            + b"".join(struct.pack("<10I", *s) for s in sh))


def strings(*items):
    """NUL-separated cp932 pool starting with padding; returns (pool, offsets)."""
    pool, offs = bytearray(4), []
    for s in items:
        offs.append(len(pool))
        pool += s.encode("cp932") + b"\0"
    pool += bytes(-len(pool) % 4)
    return bytes(pool), offs


def sample(gap=0):
    pool, offs = strings("敵を倒そう！", "ﾃｽﾄ", "OK", "%sは新しいスキルを覚えた！@n", "@c<06>ギャラリー@c<00>")
    return elf(pool, b"", offs + [offs[0]], gap), offs


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


def translated(data, ko=None, state="draft"):
    t = ebootstr.template(data)
    for e in t["entries"]:
        if ko and e["id"] in ko:
            e.update(ko=ko[e["id"]], state=state)
    return t


def test_apply_moves_translated_strings_and_keeps_the_rest():
    data, offs = sample(gap=0x100)
    out = ebootstr.apply(data, translated(data, {f"eboot:{offs[0]:#x}": "적을 쓰러뜨리자!"}), policy="dev")
    assert len(out) == len(data)
    p = prx.parse(out)
    refs = prx.pointer_refs(p, out)
    moved = [va for va in refs if va not in offs[1:]]
    assert len(moved) == 1 and len(refs[moved[0]]) == 2  # both pointers follow the string
    off = p.va_to_offset(moved[0])
    assert out[off:out.index(b"\0", off)] == kofont.encode("적을 쓰러뜨리자!")
    assert offs[3] in refs and offs[4] in refs  # untranslated strings stay where they were


def test_apply_rejects_failed_checks_and_stale_entries():
    data, offs = sample(gap=0x100)
    bad = translated(data, {f"eboot:{offs[3]:#x}": "새 스킬을 익혔다!@n"})  # %s lost
    with pytest.raises(kotext.TranslationError, match="format"):
        ebootstr.apply(data, bad, policy="dev")
    stale = translated(data, {f"eboot:{offs[0]:#x}": "적"})
    stale["entries"][0]["src_sha1"] = "000000000000"
    with pytest.raises(kotext.TranslationError, match="stale"):
        ebootstr.apply(data, stale, policy="dev")


def test_apply_release_needs_every_entry_approved():
    data, offs = sample(gap=0x100)
    with pytest.raises(kotext.TranslationError, match="release"):
        ebootstr.apply(data, translated(data, {f"eboot:{offs[0]:#x}": "적"}, state="approved"), policy="release")
def test_help_text_longer_than_four_lines_is_allowed_when_the_source_is():
    src = "@n".join(["ヘルプ"] * 6)
    assert ebootstr.check(src, "@n".join(["도움말"] * 6)) == []


def utf8_sample():
    pool = bytearray(4)
    offs = []
    for s in ("セーブデータ", "『鋼の錬金術師』のセーブデータです。\r\n情報が記録されています。", "OK"):
        offs.append(len(pool))
        pool += s.encode("utf-8") + b"\0"
    pool += bytes(-len(pool) % 4)
    return elf(bytes(pool), b"", offs), offs


def test_utf8_catalog_finds_japanese_utf8_strings():
    data, offs = utf8_sample()
    assert [(t.va, t.text) for t in ebootstr.utf8_catalog(data)] == [
        (offs[0], "セーブデータ"), (offs[1], "『鋼の錬金術師』のセーブデータです。\r\n情報が記録されています。")]


def test_apply_utf8_overwrites_within_the_original_bytes():
    data, offs = utf8_sample()
    t = ebootstr.utf8_template(data)
    t["entries"][0].update(ko="저장 데이터", state="draft")
    out = ebootstr.apply_utf8(data, t)
    p = prx.parse(out)
    off = p.va_to_offset(offs[0])
    assert out[off:out.index(b"\0", off)].decode("utf-8") == "저장 데이터"
    assert len(out) == len(data)


def test_apply_utf8_rejects_too_long_or_changed_line_breaks():
    data, offs = utf8_sample()
    t = ebootstr.utf8_template(data)
    t["entries"][0].update(ko="저장 데이터입니다", state="draft")   # 24 bytes > 18
    with pytest.raises(kotext.TranslationError, match="bytes"):
        ebootstr.apply_utf8(data, t)
    t = ebootstr.utf8_template(data)
    t["entries"][1].update(ko="저장 데이터입니다. 정보가 기록됩니다.", state="draft")  # \r\n lost
    with pytest.raises(kotext.TranslationError, match="line break"):
        ebootstr.apply_utf8(data, t)


def test_apply_overwrites_in_place_when_the_korean_fits():
    data, offs = sample(gap=0x100)
    out = ebootstr.apply(data, translated(data, {f"eboot:{offs[0]:#x}": "적"}), policy="dev")
    p = prx.parse(out)
    assert prx.pointer_refs(p, out) == prx.pointer_refs(prx.parse(data), data)  # nothing repointed
    assert p.loads[-1].filesz == prx.parse(data).loads[-1].filesz                # nothing appended
    off = p.va_to_offset(offs[0])
    assert out[off:out.index(b"\0", off)] == kofont.encode("적")
