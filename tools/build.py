"""Product build: Korean DAT000.cpk from the user's original disc files.

    python3 -m tools.build SRC_DAT000.cpk OUT_DAT000.cpk --bdf Galmuri11-Bold.bdf [--fonts ../fonts] [--policy dev|release]

Replaces FAfont14.fon (Hangul glyphs in JIS rows 16-40), every FLASH/*.srt
that has a translation file in text/ko/srt, and with --fonts the .pix files whose
textures text/ko/graphics.json redraws (D20); replaced files are stored CRILAYLA. The EBOOT is built separately
(branch poc/eboot-ui until verified on a real PSP, D7). Fails on any problem.
"""
import argparse
import json
import os
import sys

from tools import bdf, cpk, crilayla, ffon, gfxtext, kofont, kotext, textcheck

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


def graphics(arc, doc, fonts_dir):
    """Patched .pix files for the graphics text in doc (FLASH/*.pix only)."""
    def read(e):  # numba decoder: the plain one is too slow for ~650 MB of textures
        raw = arc.read_raw(e)
        return crilayla.decompress(raw) if e.compressed else raw
    files = {e.path: read(e) for e in arc.entries if e.path.startswith("FLASH/") and e.path.endswith(".pix")}
    return gfxtext.patch(files, doc, fonts_dir)


def build_dat000(src, out, bdf_path, policy, ko_dir="text/ko/srt", fonts_dir=None):
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
    n = len(repl) - 1
    gfx = os.path.join(os.path.dirname(ko_dir), "graphics.json")
    if fonts_dir and os.path.exists(gfx):
        repl.update(graphics(arc, json.load(open(gfx, encoding="utf-8")), fonts_dir))
    cpk.rebuild(src, out, repl, compress=True)
    return n, len(repl) - 1 - n


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("out")
    ap.add_argument("--bdf", required=True)
    ap.add_argument("--fonts", help="folder with the Noto KR fonts (D20); omit to keep textures as they are")
    ap.add_argument("--policy", choices=("dev", "release"), default="dev")
    a = ap.parse_args(argv)
    try:
        n, g = build_dat000(a.src, a.out, a.bdf, a.policy, fonts_dir=a.fonts)
    except kotext.TranslationError as e:
        print("\n".join(e.problems[:50]), file=sys.stderr)
        print(f"{len(e.problems)} problems; nothing written", file=sys.stderr)
        return 1
    print(f"{a.out}: font + {n} scripts + {g} texture files")
    return 0


if __name__ == "__main__":
    sys.exit(main())
