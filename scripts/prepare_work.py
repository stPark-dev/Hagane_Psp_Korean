"""Rebuild the ignored work/ directory from your own disc image.

1. Extract the ISO (ULJS00292) so that work/iso/PSP_GAME/... exists, e.g.
       7z x -owork/iso "鋼の錬金術師 約束の日へ.iso"
2. Decrypt the EBOOT with pspdecrypt (https://github.com/John-K/pspdecrypt):
       pspdecrypt work/iso/PSP_GAME/SYSDIR/EBOOT.BIN -o work/eboot/EBOOT.elf
3. Run from the repository root:
       python3 scripts/prepare_work.py
   It writes work/dat000/ (scripts and fonts from DAT000.cpk),
   work/text/srt_src.json (Japanese source of every text command) and
   work/text/eboot_names.json (speaker name plates, EBOOT table va 0x199890).
None of these files may be committed (original game data).
"""
import json
import os
import struct
import sys

sys.path.insert(0, ".")
from tools import cpk, prx, srt  # noqa: E402

DAT = "work/iso/PSP_GAME/USRDIR/DATA/DAT000.cpk"
ELF = "work/eboot/EBOOT.elf"
NAME_TABLE, NAME_COUNT = 0x199890, 1048  # speaker id -> name plate (journal: PoC-N1 follow-up)


def dump_dat000():
    arc = cpk.CpkArchive(DAT)
    for e in arc.entries:
        if e.path.lower().endswith((".pix", ".mdl", ".anmp", ".ppd")):
            continue
        p = os.path.join("work/dat000", e.path)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "wb") as f:
            f.write(arc.read(e))


def srt_sources():
    out = []
    for name in sorted(os.listdir("work/dat000/FLASH")):
        if not name.endswith(".srt"):
            continue
        s = srt.parse(open(os.path.join("work/dat000/FLASH", name), "rb").read())
        for t in s.texts():
            c = s.commands[t.index]
            ints = list(struct.unpack_from(f"<{c.argc - 1}I", c.body)) if c.argc > 1 else []
            out.append({"file": name, "idx": t.index, "op": t.op, "ints": ints, "text": t.text})
    return out


def eboot_names():
    data = open(ELF, "rb").read()
    p = prx.parse(data)
    names = []
    for i in range(NAME_COUNT):
        ptr, = struct.unpack_from("<I", data, p.va_to_offset(NAME_TABLE + 4 * i))
        if ptr == 0:
            names.append("")
            continue
        off = p.va_to_offset(ptr)
        names.append(data[off:data.index(b"\0", off)].decode("cp932"))
    return names


def main():
    dump_dat000()
    os.makedirs("work/text", exist_ok=True)
    json.dump(srt_sources(), open("work/text/srt_src.json", "w"), ensure_ascii=False)
    json.dump(eboot_names(), open("work/text/eboot_names.json", "w"), ensure_ascii=False)
    print("work/ prepared")


if __name__ == "__main__":
    main()
