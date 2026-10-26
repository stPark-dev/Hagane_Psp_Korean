import copy
import struct

import pytest

from tools import kofont, kotext, srt


def cmd(op, ints, text=None):
    body = struct.pack(f"<{len(ints)}I", *ints)
    argc = len(ints)
    if text is not None:
        raw = text.encode("cp932")
        body += raw + bytes(4 - len(raw) % 4)
        argc += 1
    return struct.pack("<III", 12 + len(body), op, argc) + body


def script():
    cmds = [cmd(0x10000, []), cmd(0, [0], "<~V1>@nあ@n⊿@n"), cmd(3, [193, 0, 0], "い@n⊿@n"),
            cmd(0x10001, [])]
    stream = b"".join(cmds)
    xsrt = b"XSRT" + struct.pack("<II", 0x10 + len(stream), len(cmds)) + bytes(4)
    body = struct.pack("<III", 1, 0, 0x14) + xsrt + stream
    return b"FSRT" + struct.pack("<I", 8 + len(body)) + body


def test_template_lists_text_entries_without_source_text():
    t = kotext.template("T001", script())
    assert t["source"] == "T001"
    assert [e["id"] for e in t["entries"]] == ["srt:T001:1", "srt:T001:2"]
    assert all(e["state"] == "untranslated" and e["ko"] == "" for e in t["entries"])
    assert "あ" not in repr(t)


def test_source_view_gives_text_and_speaker():
    v = kotext.source_view("T001", script())
    assert v[0] == {"id": "srt:T001:1", "op": 0, "speaker": 0, "src": "<~V1>@nあ@n⊿@n"}
    assert v[1]["speaker"] == 193


def translated(state="needs_review"):
    t = kotext.template("T001", script())
    t["entries"][0].update(ko="<~V1>@n가@n⊿@n", state=state)
    return t


def test_apply_dev_uses_translation_and_keeps_untranslated_source():
    out = srt.parse(kotext.apply_srt("T001", script(), translated(), policy="dev"))
    texts = [t.raw for t in out.texts()]
    assert texts == [kofont.encode("<~V1>@n가@n⊿@n"), "い@n⊿@n".encode("cp932")]


def test_apply_release_requires_every_entry_approved():
    with pytest.raises(kotext.TranslationError):
        kotext.apply_srt("T001", script(), translated("approved"), policy="release")
    t = translated("approved")
    t["entries"][1].update(ko="나@n⊿@n", state="approved")
    kotext.apply_srt("T001", script(), t, policy="release")


def test_apply_rejects_stale_source_hash():
    t = translated()
    t["entries"][0]["src_sha1"] = "0" * 12
    with pytest.raises(kotext.TranslationError, match="stale"):
        kotext.apply_srt("T001", script(), t, policy="dev")


def test_apply_rejects_broken_tokens():
    t = translated()
    t["entries"][0]["ko"] = "가@n⊿@n"  # voice cue dropped
    with pytest.raises(kotext.TranslationError, match="token"):
        kotext.apply_srt("T001", script(), t, policy="dev")


def test_apply_rejects_unknown_or_missing_ids():
    t = translated()
    t2 = copy.deepcopy(t)
    t2["entries"].pop()
    with pytest.raises(kotext.TranslationError):
        kotext.apply_srt("T001", script(), t2, policy="dev")
    t3 = copy.deepcopy(t)
    t3["entries"][0]["state"] = "done"
    with pytest.raises(kotext.TranslationError):
        kotext.apply_srt("T001", script(), t3, policy="dev")


def test_flagged_entry_is_not_release_eligible():
    t = translated("approved")
    t["entries"][1].update(ko="나@n⊿@n", state="approved", flag="의미 불명확")
    with pytest.raises(kotext.TranslationError, match="flag"):
        kotext.apply_srt("T001", script(), t, policy="release")


def test_merge_draft_updates_only_wording_flag_and_state():
    t = kotext.template("T001", script())
    out = {"srt:T001:1": {"ko": "<~V1>@n가@n⊿@n", "flag": ""},
           "srt:T001:2": {"ko": "나@n⊿@n", "flag": "화자 관계 불명확"}}
    merged = kotext.merge_draft("T001", script(), t, out)
    e1, e2 = merged["entries"]
    assert (e1["ko"], e1["state"], e1["src_sha1"]) == ("<~V1>@n가@n⊿@n", "draft", t["entries"][0]["src_sha1"])
    assert e2["flag"] == "화자 관계 불명확"
    assert t["entries"][0]["ko"] == ""  # input not mutated


def test_merge_draft_rejects_unknown_ids_and_failed_checks():
    t = kotext.template("T001", script())
    with pytest.raises(kotext.TranslationError):
        kotext.merge_draft("T001", script(), t, {"srt:T001:9": {"ko": "가", "flag": ""}})
    with pytest.raises(kotext.TranslationError, match="token"):
        kotext.merge_draft("T001", script(), t, {"srt:T001:1": {"ko": "가@n⊿@n", "flag": ""}})


def test_merge_draft_does_not_overwrite_reviewed_entries():
    t = kotext.template("T001", script())
    t["entries"][0].update(ko="<~V1>@n검수본@n⊿@n", state="needs_human_review")
    with pytest.raises(kotext.TranslationError, match="already"):
        kotext.merge_draft("T001", script(), t, {"srt:T001:1": {"ko": "<~V1>@n가@n⊿@n", "flag": ""}})
