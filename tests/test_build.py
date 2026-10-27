import pytest

from tools import build, kofont, kotext, srt
from tests.test_kotext import script


def kofile(state="draft", ko="<~V1>@n가@n⊿@n"):
    t = kotext.template("T001", script())
    t["entries"][0].update(ko=ko, state=state)
    return t


def test_translate_scripts_replaces_only_scripts_with_translations():
    raws = {"FLASH/T001.srt": script(), "FLASH/T002.srt": script()}
    out, problems = build.translate_scripts(raws, {"T001": kofile()}.get, policy="dev")
    assert problems == []
    assert set(out) == {"FLASH/T001.srt"}  # T002 has no translation file: left as is
    assert srt.parse(out["FLASH/T001.srt"]).texts()[0].raw == kofont.encode("<~V1>@n가@n⊿@n")


def test_translate_scripts_collects_problems_from_every_file():
    raws = {"FLASH/T001.srt": script(), "FLASH/T003.srt": script()}
    bad = kofile(ko="가")  # protected tokens lost
    files = {"T001": bad, "T003": bad}
    out, problems = build.translate_scripts(raws, files.get, policy="dev")
    assert out == {}
    assert any("T001" in p for p in problems) and any("T003" in p for p in problems)


def test_release_policy_refuses_drafts():
    _, problems = build.translate_scripts({"FLASH/T001.srt": script()}, {"T001": kofile()}.get, policy="release")
    assert problems and all("release" in p for p in problems)


def test_missing_glyphs_lists_characters_the_font_cannot_draw():
    from tools import ffon
    k = ffon.sjis_to_kuten(kofont.hangul_sjis("가"))
    font = ffon.Font(width=4, height=4, bpp=4, unknown_size=0, flags=bytes([1, 0]) + bytes(30),
                     single={0x41: 1}, double={k: 1}, glyphs=[bytes(8)])
    assert build.missing_glyphs(font, ["A가@n⊿@n", "<~V1>@n나‘"]) == {"나", "‘"}
