"""Product build: Korean DAT000.cpk from the user's original disc files.

    python3 -m tools.build SRC_DAT000.cpk OUT_DAT000.cpk --bdf Galmuri11-Bold.bdf [--policy dev|release]

Replaces FAfont14.fon (Hangul glyphs in JIS rows 16-40) and every FLASH/*.srt
that has a translation file in text/ko/srt. The EBOOT is built separately
(branch poc/eboot-ui until verified on a real PSP, D7). Fails on any problem.
"""
import argparse
import json
import os
import sys

from tools import bdf, cpk, ffon, kofont, kotext, textcheck

FONT = "FAfont14.fon"
BASELINE = 13  # D1/PoC-K1


def translate_scripts(raws, load_kofile, policy):
    """raws: {cpk path: srt bytes}; load_kofile(name) -> translation dict or None.
    Returns ({path: new bytes} for changed scripts, [problems])."""
    out, problems = {}, []
    for path, raw in sorted(raws.items()):
        name = os.path.splitext(os.path.basename(path))[0]
        kofile = load_kofile(name)
        if kofile is None:
            continue
        try:
            new = kotext.apply_srt(name, raw, kofile, policy)
        except kotext.TranslationError as e:
            problems.extend(f"{name}: {p}" for p in e.problems)
            continue
        if new != raw:
            out[path] = new
    return out, problems


SYMBOLS = "‘’"  # used for 『』 (D4); the game font has no glyph at their codes


def korean_font(raw, bdf_text):
    font, glyphs = ffon.parse(raw), bdf.parse(bdf_text)
    font = kofont.add_hangul(font, glyphs, kofont.KS_HANGUL, BASELINE, x_shift=kofont.HANGUL_X_SHIFT)
    font = kofont.add_symbols(font, glyphs, SYMBOLS, BASELINE, x_shift=kofont.HANGUL_X_SHIFT)
    return ffon.build(font)


def missing_glyphs(font, texts):
    """Characters in translated texts that the font has no glyph for (control tokens ignored)."""
    out = set()
    for text in texts:
        for ch in textcheck.PROTECTED.sub("", text.replace("@n", "")):
            code = kofont.encode(ch)
            if len(code) == 1:
                if code[0] >= 0x20 and code[0] != 0x20 and code[0] not in font.single:
                    out.add(ch)
            elif ffon.sjis_to_kuten(int.from_bytes(code, "big")) not in font.double:
                out.add(ch)
    return out


def build_dat000(src, out, bdf_path, policy, ko_dir="text/ko/srt"):
    arc = cpk.CpkArchive(src)
    paths = arc.by_path()

    def load(name):
        p = os.path.join(ko_dir, f"{name}.json")
        return json.load(open(p, encoding="utf-8")) if os.path.exists(p) else None

    raws = {p: arc.read(e) for p, e in paths.items() if p.startswith("FLASH/") and p.endswith(".srt")}
    repl, problems = translate_scripts(raws, load, policy)
    if problems:
        raise kotext.TranslationError(problems)
    repl[FONT] = korean_font(arc.read(paths[FONT]), open(bdf_path, encoding="utf-8").read())
    texts = [e["ko"] for n in os.listdir(ko_dir) for e in load(n[:-5])["entries"] if e["ko"]]
    ui = os.path.join(os.path.dirname(ko_dir), "eboot.json")  # the EBOOT UI draws with the same font
    if os.path.exists(ui):
        texts += [e["ko"] for e in json.load(open(ui, encoding="utf-8"))["entries"] if e["ko"]]
    lost = missing_glyphs(ffon.parse(repl[FONT]), texts)
    if lost:
        raise kotext.TranslationError([f"no glyph for {ch!r}" for ch in sorted(lost)])
    cpk.rebuild(src, out, repl)
    return len(repl) - 1


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("out")
    ap.add_argument("--bdf", required=True)
    ap.add_argument("--policy", choices=("dev", "release"), default="dev")
    a = ap.parse_args(argv)
    try:
        n = build_dat000(a.src, a.out, a.bdf, a.policy)
    except kotext.TranslationError as e:
        print("\n".join(e.problems[:50]), file=sys.stderr)
        print(f"{len(e.problems)} problems; nothing written", file=sys.stderr)
        return 1
    print(f"{a.out}: font + {n} scripts")
    return 0


if __name__ == "__main__":
    sys.exit(main())
