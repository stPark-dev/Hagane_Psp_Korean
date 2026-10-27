from tools import termlint


def g(ja, ko, state="승인", kind="term"):
    return {"ja": ja, "ko": ko, "state": state, "kind": kind}


def e(i, ko, flag="", state="draft"):
    return {"id": i, "ko": ko, "flag": flag, "state": state}


def test_missing_approved_term_is_reported():
    out = termlint.lint([e("a", "철명의 연금술사@n⊿@n"), e("b", "엉뚱한 번역@n⊿@n")],
                        {"a": "綴命の錬金術師@n⊿@n", "b": "綴命の錬金術師@n⊿@n"},
                        [g("綴命の錬金術師", "철명의 연금술사")])
    assert [(f.id, f.kind) for f in out] == [("b", "term")]


def test_line_breaks_and_spaces_do_not_hide_a_term():
    out = termlint.lint([e("a", "국가 연금술사@n“자격심사”")], {"a": "査定"}, [g("査定", "자격 심사")])
    assert out == []


def test_untranslated_entries_are_skipped():
    out = termlint.lint([e("a", "", state="untranslated")], {"a": "査定"}, [g("査定", "심사")])
    assert out == []


def test_rules_with_alternatives_or_unapproved_state_are_not_checked():
    rows = [g("殿", "님 / 공 / 양", kind="address"), g("生体錬成", "생체연성", state="제안"),
            g("を手に入れた！", "~을 손에 넣었다!", kind="system")]
    assert termlint.lint([e("a", "무관")], {"a": "殿 生体錬成 を手に入れた！"}, rows) == []


def test_pending_term_needs_a_flag():
    rows = [g("中央軍", "", state="결정필요")]
    src = {"a": "中央軍が来た", "b": "中央軍が来た"}
    out = termlint.lint([e("a", "중앙군이 왔다"), e("b", "센트럴군", flag="D7-16 보류")], src, rows)
    assert [(f.id, f.kind) for f in out] == [("a", "pending")]


def test_longest_matching_source_term_wins():
    rows = [g("中央", "중앙"), g("中央（セントラル）", "센트럴", kind="place")]
    out = termlint.lint([e("a", "센트럴에 가자")], {"a": "中央（セントラル）に行こう"}, rows)
    assert out == []


def test_long_line_is_reported_with_cell_count():
    out = termlint.lint([e("a", "가" * 23 + "@n⊿@n"), e("b", "<~V1>@n" + "가" * 22 + "@n⊿@n")],
                        {"a": "", "b": ""}, [], max_cells=22)
    assert [(f.id, f.kind) for f in out] == [("a", "width")]
    assert "23" in out[0].message


def test_katakana_term_inside_a_longer_katakana_word_is_ignored():
    rows = [g("ハン", "한", kind="name")]
    out = termlint.lint([e("a", "밥"), e("b", "밥")], {"a": "ゴハン食べた", "b": "ハンが来た"}, rows)
    assert [f.id for f in out] == ["b"]
