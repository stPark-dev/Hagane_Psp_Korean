import hashlib
import struct
from pathlib import Path

import pytest

from tools import cpk

ROOT = Path(__file__).resolve().parent.parent
DAT000 = ROOT / "work/iso/PSP_GAME/USRDIR/DATA/DAT000.cpk"
DAT001 = ROOT / "work/iso/PSP_GAME/USRDIR/DATA/DAT001.cpk"


# ---------- synthetic @UTF table ----------

def build_utf(name, columns, rows):
    """columns: list of (name, storage, type, const). rows: list of dicts."""
    strings = bytearray(b"<NULL>\0")
    str_index = {}

    def sref(s):
        if s not in str_index:
            str_index[s] = len(strings)
            strings.extend(s.encode("cp932") + b"\0")
        return str_index[s]

    fmts = {0: ">B", 2: ">H", 4: ">I", 6: ">Q"}

    def enc(ty, v):
        if ty == 0xA:
            return struct.pack(">I", sref(v))
        return struct.pack(fmts[ty], v)

    name_off = sref(name)
    schema = bytearray()
    for cname, st, ty, const in columns:
        schema += bytes([st | ty]) + struct.pack(">I", sref(cname))
        if st == 0x30:
            schema += enc(ty, const)
    rowdata = bytearray()
    rowlen = 0
    for r in rows:
        start = len(rowdata)
        for cname, st, ty, _ in columns:
            if st == 0x50:
                rowdata += enc(ty, r[cname])
        rowlen = len(rowdata) - start
    rows_off = 24 + len(schema)
    str_off = rows_off + len(rowdata)
    data_off = str_off + len(strings)
    body = struct.pack(">HHIIIHHI", 1, rows_off, str_off, data_off, name_off,
                       len(columns), rowlen, len(rows))
    body += schema + rowdata + strings
    return b"@UTF" + struct.pack(">I", len(body)) + body


def test_parse_utf_rows_and_constants():
    cols = [("FileName", 0x50, 0xA, None), ("FileSize", 0x50, 4, None),
            ("Align", 0x30, 2, 2048), ("Unused", 0x10, 4, None)]
    rows = [{"FileName": "a.srt", "FileSize": 10},
            {"FileName": "デモ.pix", "FileSize": 0xDEADBEEF}]
    name, out = cpk.parse_utf(build_utf("CpkTocInfo", cols, rows))
    assert name == "CpkTocInfo"
    assert out == [
        {"FileName": "a.srt", "FileSize": 10, "Align": 2048, "Unused": None},
        {"FileName": "デモ.pix", "FileSize": 0xDEADBEEF, "Align": 2048, "Unused": None},
    ]


def test_parse_utf_rejects_bad_magic():
    with pytest.raises(ValueError):
        cpk.parse_utf(b"XXXX" + bytes(40))


# ---------- synthetic CRILAYLA ----------

def build_crilayla(prefix, tokens):
    """prefix: first 0x100 output bytes (stored raw).
    tokens: in decode order (output is produced from the end backwards);
    ('lit', b) or ('ref', distance, length) with length 3..9."""
    bits = []

    def put(v, n):
        bits.extend((v >> (n - 1 - i)) & 1 for i in range(n))

    usize = 0
    for t in tokens:
        if t[0] == "lit":
            put(0, 1); put(t[1], 8); usize += 1
        else:
            _, dist, length = t
            put(1, 1); put(dist - 3, 13)
            extra = length - 3
            assert 0 <= extra < 3
            put(extra, 2)
            usize += length
    while len(bits) % 8:
        bits.append(0)
    stream = bytes(int("".join(map(str, bits[i:i + 8])), 2) for i in range(0, len(bits), 8))
    comp = stream[::-1]  # consumed from the end downward
    return (b"CRILAYLA" + struct.pack("<II", usize, len(comp)) + comp + prefix)


def test_crilayla_literals_are_written_backwards():
    prefix = bytes(range(256))
    data = build_crilayla(prefix, [("lit", 0x41), ("lit", 0x42), ("lit", 0x43)])
    assert cpk.decompress_crilayla(data) == prefix + b"CBA"


def test_crilayla_backref_copies_already_written_tail():
    prefix = bytes(256)
    # decode order: write 'Z','Y','X' at the end, then copy 3 bytes from distance 3
    data = build_crilayla(prefix, [("lit", 0x5A), ("lit", 0x59), ("lit", 0x58), ("ref", 3, 3)])
    assert cpk.decompress_crilayla(data) == prefix + b"XYZXYZ"


def test_crilayla_rejects_bad_magic():
    with pytest.raises(ValueError):
        cpk.decompress_crilayla(b"NOTLAYLA" + bytes(300))


# ---------- real archives (only when the extracted disc is present) ----------

needs_dat000 = pytest.mark.skipif(not DAT000.exists(), reason="extracted disc not present")
needs_dat001 = pytest.mark.skipif(not DAT001.exists(), reason="extracted disc not present")


@needs_dat000
def test_dat000_toc_lists_all_files():
    arc = cpk.CpkArchive(DAT000)
    assert arc.header["Files"] == 4968
    assert len(arc.entries) == 4968
    assert all(e.path for e in arc.entries)


@needs_dat000
def test_dat000_compressed_entry_expands_to_extract_size():
    arc = cpk.CpkArchive(DAT000)
    e = next(e for e in arc.entries if e.path.endswith(".srt") and e.compressed)
    assert len(arc.read(e)) == e.extract_size


@needs_dat001
def test_dat001_itoc_lists_all_files():
    arc = cpk.CpkArchive(DAT001)
    assert len(arc.entries) == arc.header["Files"] == 4411
    offs = [e.offset for e in arc.entries]
    assert offs == sorted(offs)
    last = arc.entries[-1]
    assert last.offset + last.size <= DAT001.stat().st_size


# ---------- rebuild ----------

def test_parse_utf_positions_point_at_row_cells():
    cols = [("FileName", 0x50, 0xA, None), ("FileSize", 0x50, 4, None)]
    rows = [{"FileName": "a", "FileSize": 7}, {"FileName": "b", "FileSize": 9}]
    buf = build_utf("T", cols, rows)
    _, _, pos = cpk.parse_utf_positions(buf)
    off, fmt = pos[1]["FileSize"]
    assert struct.unpack_from(fmt, buf, off)[0] == 9


@needs_dat000
def test_dat000_unchanged_rebuild_is_byte_identical(tmp_path):
    out = tmp_path / "DAT000.cpk"
    cpk.rebuild(DAT000, out, {})
    assert out.stat().st_size == DAT000.stat().st_size
    assert hashlib.sha256(out.read_bytes()).digest() == hashlib.sha256(DAT000.read_bytes()).digest()


@needs_dat000
def test_dat000_rebuild_with_replacement(tmp_path):
    src = cpk.CpkArchive(DAT000)
    target = next(e for e in src.entries if e.path == "FAfont14.fon")
    other = next(e for e in src.entries if e.path.endswith(".srt"))
    new = b"\x5a" * (target.extract_size + 5000)  # grows past the old slot
    out = tmp_path / "DAT000.cpk"
    cpk.rebuild(DAT000, out, {"FAfont14.fon": new})
    arc = cpk.CpkArchive(out)
    e = next(e for e in arc.entries if e.path == "FAfont14.fon")
    assert not e.compressed and arc.read(e) == new
    o = next(e for e in arc.entries if e.path == other.path)
    assert arc.read(o) == src.read(other)
    h = arc.header
    assert h["EnabledDataSize"] == sum(x.size + x.extract_size for x in arc.entries)
    assert h["EnabledPackedSize"] == 2 * sum(x.extract_size for x in arc.entries)
    assert h["ContentSize"] == -(-(out.stat().st_size - h["ContentOffset"]) // 2048) * 2048
    assert all(x.offset % 2048 == 0 for x in arc.entries)


@needs_dat000
def test_rebuild_rejects_unknown_path(tmp_path):
    with pytest.raises(KeyError):
        cpk.rebuild(DAT000, tmp_path / "x.cpk", {"no/such.file": b""})


@needs_dat000
def test_rebuild_can_store_replacements_compressed(tmp_path):
    src = cpk.CpkArchive(DAT000)
    target = next(e for e in src.entries if e.path == "FLASH/ID/g_menu.pix")
    new = bytearray(src.read(target))
    new[0x1000:0x1010] = b"\x11" * 16
    out = tmp_path / "DAT000.cpk"
    cpk.rebuild(DAT000, out, {target.path: bytes(new)}, compress=True)
    arc = cpk.CpkArchive(out)
    e = arc.by_path()[target.path]
    assert e.compressed and e.extract_size == len(new) and e.size < len(new) // 2
    assert arc.read(e) == new


@needs_dat000
def test_rebuild_keeps_a_grown_file_uncompressed(tmp_path):
    # a grown compressed file hangs the game's loader (Korean FAfont14.fon), so it is stored raw
    src = cpk.CpkArchive(DAT000)
    target = src.by_path()["FAfont14.fon"]
    assert target.compressed
    new = src.read(target) * 2
    out = tmp_path / "DAT000.cpk"
    cpk.rebuild(DAT000, out, {target.path: new}, compress=True)
    e = cpk.CpkArchive(out).by_path()[target.path]
    assert not e.compressed and e.size == len(new)


@needs_dat001
def test_overwrite_same_size_changes_only_that_file(tmp_path):
    arc = cpk.CpkArchive(DAT001)
    e = arc.by_path()["00058"]
    new = bytes(reversed(arc.read(e)))
    out = tmp_path / "DAT001.cpk"
    cpk.overwrite_same_size(DAT001, out, {"00058": new})
    assert out.stat().st_size == DAT001.stat().st_size
    got = cpk.CpkArchive(out)
    assert got.read(got.by_path()["00058"]) == new
    assert got.read(got.by_path()["00057"]) == arc.read(arc.by_path()["00057"])


@needs_dat001
def test_overwrite_same_size_rejects_other_sizes(tmp_path):
    with pytest.raises(ValueError):
        cpk.overwrite_same_size(DAT001, tmp_path / "x.cpk", {"00058": b"short"})
