from tools import textcheck


def test_identical_tokens_pass():
    src = "<~V1>@nあ@n⊥@n<~V2>@nい@n⊿@n"
    ko = "<~V1>@n가@n나@n⊥@n<~V2>@n다@n⊿@n"
    assert textcheck.check(src, ko) == []


def test_missing_voice_cue_is_reported():
    errs = textcheck.check("<~V1>@nあ@n⊿@n", "가@n⊿@n")
    assert any("token" in e for e in errs)


def test_reordered_page_controls_are_reported():
    errs = textcheck.check("あ@n⊥@nい@n⊿@n", "가@n⊿@n나@n⊥@n")
    assert errs


def test_colour_arguments_must_match():
    errs = textcheck.check("@c<00>あ@c<08>い@c<00>", "@c<00>가@c<07>나@c<00>")
    assert errs


def test_unencodable_character_is_reported():
    errs = textcheck.check("あ@n⊿@n", "똠@n⊿@n")
    assert any("encode" in e for e in errs)


def test_page_line_limit():
    src = "あ@n⊿@n"
    ko = "가@n나@n다@n라@n마@n⊿@n"
    assert any("lines" in e for e in textcheck.check(src, ko, max_lines=4))
    assert textcheck.check(src, "가@n나@n다@n라@n⊿@n", max_lines=4) == []


def test_line_breaks_may_move():
    assert textcheck.check("あい@nう@n⊿@n", "가@n나다라@n⊿@n") == []
