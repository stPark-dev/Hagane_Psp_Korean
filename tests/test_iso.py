import hashlib
import struct
from pathlib import Path

import pytest

from tools import iso

ORIG = Path(__file__).resolve().parent.parent / "original" / "Hagane no Renkinjutsushi - Yakusoku no Hi e (Japan).iso"
S = 2048


def both32(v):
    return struct.pack("<I", v) + struct.pack(">I", v)


def record(name, lba, size, is_dir):
    n = name.encode()
    body = (bytes([0]) + both32(lba) + both32(size) + bytes(7) + bytes([2 if is_dir else 0])
            + bytes(2) + struct.pack("<H", 1) + struct.pack(">H", 1) + bytes([len(n)]) + n)
    if len(n) % 2 == 0:
        body += b"\0"
    return bytes([len(body) + 1]) + body


def tiny_iso():
    """sector 16 PVD, 17 terminator, 18 root dir, 19 SUB dir, 20-21 A.BIN (3000 B), 22 B.BIN (10 B)."""
    img = bytearray(23 * S)
    root = record("\0", 18, S, True) + record("\1", 18, S, True) + record("SUB", 19, S, True) + record("A.BIN;1", 20, 3000, False)
    sub = record("\0", 19, S, True) + record("\1", 18, S, True) + record("B.BIN;1", 22, 10, False)
    pvd = bytearray(S)
    pvd[0:6] = b"\x01CD001"
    pvd[156:156 + 34] = record("\0", 18, S, True)
    img[16 * S:17 * S] = pvd
    img[17 * S:17 * S + 6] = b"\xffCD001"
    img[18 * S:18 * S + len(root)] = root
    img[19 * S:19 * S + len(sub)] = sub
    img[20 * S:20 * S + 3000] = b"A" * 3000
    img[22 * S:22 * S + 10] = b"B" * 10
    return bytes(img)


def test_files_lists_paths_with_extent_and_size():
    f = iso.files(tiny_iso())
    assert f["A.BIN"].lba == 20 and f["A.BIN"].size == 3000
    assert f["SUB/B.BIN"].lba == 22 and f["SUB/B.BIN"].size == 10


def test_replace_writes_in_place_and_updates_the_size(tmp_path):
    src = tmp_path / "a.iso"
    src.write_bytes(tiny_iso())
    out = tmp_path / "b.iso"
    iso.replace(src, out, {"A.BIN": b"x" * 4000, "SUB/B.BIN": b"y" * 5})
    img = out.read_bytes()
    assert len(img) == len(tiny_iso())
    f = iso.files(img)
    assert f["A.BIN"].size == 4000 and img[20 * S:20 * S + 4000] == b"x" * 4000 and img[20 * S + 4000:22 * S] == bytes(96)
    assert f["SUB/B.BIN"].size == 5 and img[22 * S:22 * S + 10] == b"y" * 5 + bytes(5)


def test_replace_refuses_data_larger_than_the_allocated_sectors(tmp_path):
    src = tmp_path / "a.iso"
    src.write_bytes(tiny_iso())
    with pytest.raises(ValueError):
        iso.replace(src, tmp_path / "b.iso", {"SUB/B.BIN": b"z" * (S + 1)})


@pytest.mark.skipif(not ORIG.exists(), reason="original disc image not present")
def test_real_iso_lists_the_game_files():
    with open(ORIG, "rb") as fh:
        head = fh.read(4 * 1024 * 1024)
    f = iso.files(head)
    assert f["PSP_GAME/USRDIR/DATA/DAT000.cpk"].size == 308876756
    assert f["PSP_GAME/SYSDIR/EBOOT.BIN"].size == 2892160
