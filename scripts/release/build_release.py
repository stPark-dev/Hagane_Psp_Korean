"""Build a release: patched ISO from the user's original ISO, then a patch against it.

    python3 scripts/release/build_release.py --version 0.9 \
        [--iso original/<ULJS00292>.iso] [--elf work/eboot/EBOOT.elf] [--out dist]

Steps: check the original ISO's SHA-256 (docs/survey.md), build DAT000 (dialogue, font, graphics
text) and the Korean EBOOT (UI strings + system-screen UTF-8 strings) from the repository, write both
over their own sectors in a copy of the ISO (tools/iso.py), then make an xdelta3 patch if xdelta3 is
installed. The ISO and every game file stay in --out (git-ignored) and are never distributed; only
the .xdelta and the text files in dist/<name>/ are.
Policy is 'dev' (draft translations allowed) for 0.x betas, see docs/decisions.md D21.
"""
import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile

sys.path.insert(0, ".")
from tools import build, ebootstr, iso  # noqa: E402

ORIGINAL_SHA256 = "158449b7eced76fb6fc3c739956ab675154bba7825d0afcea9f2d257fb15a4fe"
ISO_NAME = "Hagane no Renkinjutsushi - Yakusoku no Hi e (Japan).iso"
DAT000, EBOOT = "PSP_GAME/USRDIR/DATA/DAT000.cpk", "PSP_GAME/SYSDIR/EBOOT.BIN"


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def korean_eboot(elf_path):
    data = open(elf_path, "rb").read()
    data = ebootstr.apply(data, json.load(open("text/ko/eboot.json", encoding="utf-8")), "dev")
    data = data[0] if isinstance(data, tuple) else data
    data = ebootstr.apply_utf8(data, json.load(open("text/ko/eboot_utf8.json", encoding="utf-8")))
    return data[0] if isinstance(data, tuple) else data


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--version", required=True)
    ap.add_argument("--iso", default=os.path.join("original", ISO_NAME))
    ap.add_argument("--elf", default="work/eboot/EBOOT.elf")
    ap.add_argument("--bdf", default="../galmuri/Galmuri11-Bold.bdf")
    ap.add_argument("--fonts", default="../fonts")
    ap.add_argument("--out", default="dist")
    a = ap.parse_args()

    if sha256(a.iso) != ORIGINAL_SHA256:
        raise SystemExit(f"{a.iso}: not the expected original ISO (SHA-256 {ORIGINAL_SHA256})")
    name = f"Hagane_Yakusoku_KR_v{a.version}"
    os.makedirs(a.out, exist_ok=True)
    patched = os.path.join(a.out, f"{name}.iso")
    with tempfile.TemporaryDirectory() as tmp:
        src_dat = os.path.join(tmp, "DAT000.src.cpk")
        with open(a.iso, "rb") as fh:
            f = iso.files(fh)[DAT000]
            fh.seek(f.lba * iso.SECTOR)
            open(src_dat, "wb").write(fh.read(f.size))
        new_dat = os.path.join(tmp, "DAT000.cpk")
        build.build_dat000(src_dat, new_dat, a.bdf, "dev", fonts_dir=a.fonts)
        iso.replace(a.iso, patched, {DAT000: open(new_dat, "rb").read(), EBOOT: korean_eboot(a.elf)})
    print(f"{patched}: SHA-256 {sha256(patched)}")

    pkg = os.path.join(a.out, name)
    os.makedirs(pkg, exist_ok=True)
    for doc in ("README.txt", "LICENSES.txt"):
        shutil.copy(os.path.join("docs", "release", doc), pkg)
    with open(os.path.join(pkg, "CHECKSUMS.txt"), "w", encoding="utf-8") as c:
        c.write(f"원본 ISO SHA-256: {ORIGINAL_SHA256}\n패치 적용 후 ISO SHA-256: {sha256(patched)}\n"
                f"패치 적용 후 ISO 크기: {os.path.getsize(patched):,} 바이트\n")
    if shutil.which("xdelta3"):
        delta = os.path.join(pkg, f"{name}.xdelta")
        subprocess.run(["xdelta3", "-e", "-9", "-f", "-S", "djw", "-s", a.iso, patched, delta], check=True)
        print(f"{delta}: {os.path.getsize(delta):,} bytes")
    else:
        print("xdelta3 not installed: patched ISO built, patch file not made")


if __name__ == "__main__":
    main()
