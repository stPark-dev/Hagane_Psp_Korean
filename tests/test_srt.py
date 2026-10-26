import struct
from pathlib import Path

import pytest

from tools import srt

ROOT = Path(__file__).resolve().parent.parent
FLASH = ROOT / "work/dat000/FLASH"


def cmd(op, ints, text=None):
    body = struct.pack(f"<{len(ints)}I", *ints)
    argc = len(ints)
    if text is not None:
        raw = text.encode("cp932")
        body += raw + bytes(4 - len(raw) % 4)
        argc += 1
    return struct.pack("<III", 12 + len(body), op, argc) + body


def script(cmds):
    stream = b"".join(cmds)
    xsrt = b"XSRT" + struct.pack("<II", 0x10 + len(stream), len(cmds)) + bytes(4)
    body = struct.pack("<III", 1, 0, 0x14) + xsrt + stream
    return b"FSRT" + struct.pack("<I", 8 + len(body)) + body


def sample():
    # 0: start, 1: text, 2: goto -> cmd 4, 3: text, 4: end
    c0 = cmd(0x10000, [])
    c1 = cmd(3, [0x30, 5, 1], "<~M0011_x>@nあ@n⊿@n")
    c3 = cmd(0, [7], "い")
    c4 = cmd(0x10001, [])
    goto_target = len(c0) + len(c1) + len(cmd(0x10008, [0])) + len(c3)
    c2 = cmd(0x10008, [goto_target])
    return script([c0, c1, c2, c3, c4])


def test_parse_lists_text_commands():
    s = srt.parse(sample())
    assert [(t.index, t.op, t.text) for t in s.texts()] == [(1, 3, "<~M0011_x>@nあ@n⊿@n"), (3, 0, "い")]


def test_unchanged_build_is_identical():
    raw = sample()
    assert srt.build(srt.parse(raw)) == raw


def test_longer_text_relocates_branch_targets():
    s = srt.parse(sample())
    s.set_text(1, b"ABCDEFGHIJKL")
    out = srt.parse(srt.build(s))
    goto = out.commands[2]
    assert goto.op == 0x10008
    assert goto.int_arg(0) == out.offset_of(4)
    assert out.commands[1].int_arg(0) == 0x30  # integer params kept in front of the text
    assert out.texts()[0].raw == b"ABCDEFGHIJKL"


def test_padding_always_keeps_a_terminator():
    s = srt.parse(sample())
    s.set_text(3, b"ABCD")
    body = srt.parse(srt.build(s)).commands[3].body
    assert body == struct.pack("<I", 7) + b"ABCD\0\0\0\0"


def test_branch_to_non_command_offset_is_rejected():
    raw = bytearray(sample())
    # point the goto into the middle of command 1
    goto_off = 0x24 + srt.parse(bytes(raw)).offset_of(2)
    struct.pack_into("<I", raw, goto_off + 12, 6)
    with pytest.raises(ValueError):
        srt.build(srt.parse(bytes(raw)))


def test_set_text_rejects_non_text_command():
    s = srt.parse(sample())
    with pytest.raises(ValueError):
        s.set_text(2, b"x")


@pytest.mark.skipif(not FLASH.exists(), reason="extracted scripts not present")
def test_all_real_scripts_roundtrip():
    files = sorted(FLASH.glob("*.srt"))
    assert len(files) == 613
    for p in files:
        raw = p.read_bytes()
        assert srt.build(srt.parse(raw)) == raw, p.name


@pytest.mark.skipif(not FLASH.exists(), reason="extracted scripts not present")
def test_real_text_starts_at_the_string_parameter():
    s = srt.parse((FLASH / "M001_1.srt").read_bytes())
    first = s.texts()[0]
    assert first.text.startswith("<~M0011_rdi01a>@nこの地上に生ける神の子らよ。")
    for p in sorted(FLASH.glob("*.srt")):
        for t in srt.parse(p.read_bytes()).texts():
            text = t.text  # every text decodes as Shift-JIS
            assert not text.startswith("011_"), (p.name, t.index)
