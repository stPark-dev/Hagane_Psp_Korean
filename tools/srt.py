"""FSRT/XSRT event scripts (FLASH/*.srt).

  0x00 'FSRT' u32 file size, u32 1, u32 0, u32 0x14
  0x14 'XSRT' u32 size from 0x14, u32 command count, u32 0
  0x24 commands: u32 size, u32 op, u32 argc, parameters
Parameters are u32 integers or inline strings (NUL padded to the next 4-byte
boundary with at least one NUL); argc counts both. Text commands are argc-1
integers followed by one Shift-JIS string. Branch commands hold byte offsets
relative to 0x24 that must follow the commands when sizes change.
"""
import struct
from dataclasses import dataclass

STREAM_START = 0x24

# op -> argc of commands whose last parameter is display text
TEXT_OPS = {0x0: 2, 0x1: 2, 0x2: 2, 0x3: 4, 0x4: 4, 0x5: 4, 0x6: 4, 0x7: 4,
            0x1D: 2, 0x1E: 2, 0x1F: 2, 0x21: 2, 0x3A: 2, 0x3B: 2, 0x3C: 2, 0x6E: 2}

# op -> index of the integer parameter holding a branch target
# 0x10002/0x10003 case, 0x10004 (case-like), 0x1000B default, 0x10008 goto
BRANCH_ARG = {0x10002: 1, 0x10003: 1, 0x10004: 1, 0x1000B: 1, 0x10008: 0}


@dataclass(frozen=True)
class Command:
    op: int
    argc: int
    body: bytes  # parameters as stored

    def size(self):
        return 12 + len(self.body)

    def int_arg(self, i):
        return struct.unpack_from("<I", self.body, 4 * i)[0]

    def with_int_arg(self, i, value):
        body = bytearray(self.body)
        struct.pack_into("<I", body, 4 * i, value)
        return Command(self.op, self.argc, bytes(body))

    def encode(self):
        return struct.pack("<III", self.size(), self.op, self.argc) + self.body


@dataclass(frozen=True)
class Text:
    index: int
    op: int
    raw: bytes

    @property
    def text(self):
        return self.raw.decode("cp932")


def pad_text(raw):
    if b"\0" in raw:
        raise ValueError("text must not contain NUL")
    return raw + bytes(4 - len(raw) % 4)


def _text_start(c):
    return 4 * (c.argc - 1)


class Script:
    def __init__(self, header, commands, targets):
        self.header = header
        self.commands = commands
        self.targets = targets  # branch command index -> target command index

    def offset_of(self, index):
        return sum(c.size() for c in self.commands[:index])

    def is_text(self, index):
        c = self.commands[index]
        return TEXT_OPS.get(c.op) == c.argc

    def texts(self):
        out = []
        for i, c in enumerate(self.commands):
            if self.is_text(i):
                out.append(Text(i, c.op, c.body[_text_start(c):].split(b"\0", 1)[0]))
        return out

    def set_text(self, index, raw):
        if not self.is_text(index):
            raise ValueError(f"command {index} is not a text command")
        c = self.commands[index]
        self.commands[index] = Command(c.op, c.argc, c.body[:_text_start(c)] + pad_text(raw))


def parse(buf):
    if buf[:4] != b"FSRT" or buf[0x14:0x18] != b"XSRT":
        raise ValueError("not an FSRT/XSRT script")
    fsize, = struct.unpack_from("<I", buf, 4)
    xsize, count = struct.unpack_from("<II", buf, 0x18)
    if fsize != len(buf) or xsize != len(buf) - 0x14:
        raise ValueError("script size fields disagree with the file size")
    cmds = []
    starts = {}
    pos = STREAM_START
    while pos < len(buf):
        size, op, argc = struct.unpack_from("<III", buf, pos)
        if size < 12 or pos + size > len(buf):
            raise ValueError(f"bad command at {pos:#x}")
        starts[pos - STREAM_START] = len(cmds)
        cmds.append(Command(op, argc, bytes(buf[pos + 12:pos + size])))
        pos += size
    if len(cmds) != count:
        raise ValueError(f"{len(cmds)} commands, header says {count}")
    targets = {}
    for i, c in enumerate(cmds):
        if c.op in BRANCH_ARG:
            if len(c.body) != 4 * c.argc:
                raise ValueError(f"command {i}: branch op {c.op:#x} with non-integer parameters")
            off = c.int_arg(BRANCH_ARG[c.op])
            if off not in starts:
                raise ValueError(f"command {i} (op {c.op:#x}) branches to {off:#x}, not a command start")
            targets[i] = starts[off]
        if TEXT_OPS.get(c.op) == c.argc:
            tail = c.body[_text_start(c):]
            if tail != pad_text(tail.split(b"\0", 1)[0]):
                raise ValueError(f"command {i}: unexpected text padding")
    return Script(bytes(buf[:STREAM_START]), cmds, targets)


def build(script):
    offsets = []
    pos = 0
    for c in script.commands:
        offsets.append(pos)
        pos += c.size()

    def relocated(i, c):
        if i not in script.targets:
            return c
        return c.with_int_arg(BRANCH_ARG[c.op], offsets[script.targets[i]])

    stream = b"".join(relocated(i, c).encode() for i, c in enumerate(script.commands))
    head = bytearray(script.header)
    total = STREAM_START + len(stream)
    struct.pack_into("<I", head, 4, total)
    struct.pack_into("<II", head, 0x18, total - 0x14, len(script.commands))
    return bytes(head) + stream
