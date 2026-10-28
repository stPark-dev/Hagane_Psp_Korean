"""ISO 9660 images (the UMD .iso): list files and overwrite them in place.

replace() keeps the disc layout: each new file goes into the sectors the old one occupied (it may
not be larger than them), the rest of those sectors is zeroed, and the size in its directory record
is updated. Nothing else in the image changes, so a patch against the original stays small.
"""
import shutil
import struct
from dataclasses import dataclass

SECTOR = 2048


@dataclass
class File:
    path: str
    lba: int
    size: int
    record: int        # byte offset of the directory record in the image

    @property
    def allocated(self):
        return -(-self.size // SECTOR) * SECTOR


def _read(img, pos, n):
    if isinstance(img, (bytes, bytearray)):
        return img[pos:pos + n]
    img.seek(pos)
    return img.read(n)


def files(img):
    """{path: File} for every file, from bytes or a binary file object."""
    pvd = _read(img, 16 * SECTOR, SECTOR)
    if pvd[1:6] != b"CD001":
        raise ValueError("not an ISO 9660 image")
    out = {}

    def walk(lba, size, prefix):
        data = _read(img, lba * SECTOR, size)
        pos = 0
        while pos < len(data):
            n = data[pos]
            if n == 0:                                   # records don't cross sectors
                pos = (pos // SECTOR + 1) * SECTOR
                continue
            ext, length = struct.unpack_from("<I", data, pos + 2)[0], struct.unpack_from("<I", data, pos + 10)[0]
            flags, name_len = data[pos + 25], data[pos + 32]
            name = data[pos + 33:pos + 33 + name_len]
            if name not in (b"\0", b"\1"):
                name = name.decode("ascii").split(";")[0]
                path = prefix + name
                if flags & 2:
                    walk(ext, length, path + "/")
                else:
                    out[path] = File(path, ext, length, lba * SECTOR + pos)
            pos += n

    root = pvd[156:190]
    walk(struct.unpack_from("<I", root, 2)[0], struct.unpack_from("<I", root, 10)[0], "")
    return out


def replace(src, out, replacements):
    """Copy src to out with each {path: bytes} written over that file's own sectors."""
    with open(src, "rb") as fh:
        index = files(fh)
    for path, data in replacements.items():
        f = index.get(path)
        if f is None:
            raise ValueError(f"{path}: not in {src}")
        if len(data) > f.allocated:
            raise ValueError(f"{path}: {len(data)} bytes do not fit its {f.allocated} allocated bytes")
    shutil.copyfile(src, out)
    with open(out, "r+b") as fh:
        for path, data in replacements.items():
            f = index[path]
            fh.seek(f.lba * SECTOR)
            fh.write(data + bytes(f.allocated - len(data)))
            fh.seek(f.record + 10)
            fh.write(struct.pack("<I", len(data)) + struct.pack(">I", len(data)))
