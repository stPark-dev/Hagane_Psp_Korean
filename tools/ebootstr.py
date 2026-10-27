"""UI strings in the decrypted EBOOT and their Korean translation file.

The game reaches its UI text through R_MIPS_32 pointers (tables in .data).
A catalog entry is a clean Japanese cp932 string in .rodata/.data that a
pointer targets and that starts right after a NUL. Strings reached only
through HI16/LO16 code pairs are debug messages and are left out.

text/ko/eboot.json mirrors text/ko/srt: id (eboot:<address>), hash of the
source bytes, Korean, review state and flag; the source text stays out of
the repository and is regenerated from the user's EBOOT.
"""
import re
from dataclasses import dataclass

from tools import kofont, kotext, prx, textcheck

STRING_SECTIONS = (".rodata", ".data")
JAPANESE = re.compile("[぀-ヿ一-鿿！-～]")
NOT_TEXT = re.compile("[\x00-\x1f｡-ﾟ]")  # control bytes, half-width kana: data, not text
FORMAT = re.compile(r"%[-0-9.]*[a-zA-Z]")
BUTTONS = re.compile("[∈∋⊆⊇↑↓←→]")  # glyph slots the game draws as button icons


@dataclass(frozen=True)
class Text:
    va: int
    raw: bytes
    refs: tuple
    encoding: str = "cp932"

    @property
    def text(self):
        return self.raw.decode(self.encoding)

    @property
    def id(self):
        return f"eboot:{self.va:#x}"


def _string_at(p, data, va):
    off = p.va_to_offset(va)
    if off == 0 or data[off - 1] != 0:
        return None
    raw = data[off:data.index(b"\0", off)]
    try:
        text = raw.decode("cp932")
    except UnicodeDecodeError:
        return None
    if not JAPANESE.search(text) or NOT_TEXT.search(text):
        return None
    return raw


def catalog(data):
    p = prx.parse(data)
    areas = [(s.addr, s.addr + s.size) for s in prx.sections(data) if s.name in STRING_SECTIONS]
    out = []
    for va, refs in sorted(prx.pointer_refs(p, data).items()):
        if not any(a <= va < b for a, b in areas):
            continue
        raw = _string_at(p, data, va)
        if raw is not None:
            out.append(Text(va, raw, tuple(refs)))
    return out


def template(data):
    return {"source": "EBOOT",
            "entries": [{"id": t.id, "src_sha1": kotext.src_hash(t.raw), "ko": "",
                         "state": "untranslated", "flag": ""} for t in catalog(data)]}


CODES = re.compile(r"@[cs]<[^>]*>")


def line_widths(text):
    """Display width per @n line: full-width (Japanese, Hangul) 2, half-width 1, colour/speed codes 0."""
    lines = CODES.sub("", text).split("@n")
    return [sum(1 if ord(ch) < 0x80 or 0xFF61 <= ord(ch) <= 0xFF9F else 2 for ch in line) for line in lines]


def wider_lines(src, ko):
    """[(line number, ko width, source width)] where the Korean line is wider than the source line."""
    s, k = line_widths(src), line_widths(ko)
    return [(i + 1, w, s[i] if i < len(s) else 0) for i, w in enumerate(k)
            if w > (s[i] if i < len(s) else 0)]


def check(src, ko):
    errs = textcheck.check(src, ko, max_lines=max(4, src.count("@n") + 1))  # UI text has no 4-line pages
    for name, pat in (("format", FORMAT), ("button glyph", BUTTONS)):
        if pat.findall(src) != pat.findall(ko):
            errs.append(f"{name} sequence differs: {pat.findall(src)} != {pat.findall(ko)}")
    return errs


def apply(data, kofile, policy):
    """Return the EBOOT with translated strings moved in (prx.move_strings);
    raise kotext.TranslationError on any mismatch or check failure.
    Branch poc/eboot-strings only until verified on a real PSP (D7)."""
    if policy not in ("dev", "release"):
        raise ValueError(policy)
    texts = {t.id: t for t in catalog(data)}
    entries = {e["id"]: e for e in kofile["entries"]}
    problems = []
    if kofile.get("source") != "EBOOT":
        problems.append(f"file is for {kofile.get('source')!r}, not 'EBOOT'")
    problems += [f"{i}: missing from translation file" for i in sorted(set(texts) - set(entries))]
    problems += [f"{i}: not a catalog string" for i in sorted(set(entries) - set(texts))]
    strings = {}
    for i, t in texts.items():
        e = entries.get(i)
        if e is None:
            continue
        if e["src_sha1"] != kotext.src_hash(t.raw):
            problems.append(f"{i}: stale translation (source text changed)")
            continue
        if policy == "release" and (e["state"] != "approved" or e.get("flag")):
            problems.append(f"{i}: not release eligible (state {e['state']}, flag {e.get('flag', '')!r})")
            continue
        if e["state"] not in kotext.DEV_STATES:
            continue
        errs = check(t.text, e["ko"])
        if errs:
            problems.extend(f"{i}: {err}" for err in errs)
            continue
        strings[t.va] = kofont.encode(e["ko"])
    if problems:
        raise kotext.TranslationError(problems)
    return prx.move_strings(data, strings)[0]


UTF8_JAPANESE = re.compile("[぀-ヿ]")
LINE_BREAKS = re.compile("\r\n")  # dialog layout; bare \n in titles may be rearranged


def utf8_catalog(data):
    """UTF-8 Japanese strings (system dialogs and save/install data info, drawn by the PSP system font)."""
    p = prx.parse(data)
    areas = [(s.addr, s.addr + s.size) for s in prx.sections(data) if s.name in STRING_SECTIONS]
    out = []
    for a, b in areas:
        off0 = p.va_to_offset(a)
        chunk = data[off0:off0 + (b - a)]
        pos = 0
        for raw in chunk.split(b"\0"):
            start, pos = pos, pos + len(raw) + 1
            if not raw or (start == 0 and off0 and data[off0 - 1] != 0):
                continue
            try:
                text = raw.decode("utf-8")
            except UnicodeDecodeError:
                continue
            if UTF8_JAPANESE.search(text) and not re.search("[\x00-\x09\x0b\x0c\x0e-\x1f]", text):
                out.append(Text(a + start, raw, (), "utf-8"))
    return out


def utf8_template(data):
    return {"source": "EBOOT-UTF8",
            "entries": [{"id": f"eboot8:{t.va:#x}", "src_sha1": kotext.src_hash(t.raw), "ko": "",
                         "state": "untranslated", "flag": ""} for t in utf8_catalog(data)]}


def apply_utf8(data, kofile):
    """Overwrite translated UTF-8 strings in place (prx.overwrite). Branch only (D19 addendum)."""
    texts = {f"eboot8:{t.va:#x}": t for t in utf8_catalog(data)}
    problems, strings = [], {}
    for e in kofile["entries"]:
        t = texts.get(e["id"])
        if t is None:
            problems.append(f"{e['id']}: not a UTF-8 catalog string"); continue
        if e["src_sha1"] != kotext.src_hash(t.raw):
            problems.append(f"{e['id']}: stale translation (source text changed)"); continue
        if e["state"] not in kotext.DEV_STATES:
            continue
        new = e["ko"].encode("utf-8")
        if len(new) > len(t.raw):
            problems.append(f"{e['id']}: {len(new)} bytes, only {len(t.raw)} bytes available"); continue
        if LINE_BREAKS.findall(t.text) != LINE_BREAKS.findall(e["ko"]):
            problems.append(f"{e['id']}: line break sequence differs"); continue
        strings[t.va] = new
    if problems:
        raise kotext.TranslationError(problems)
    return prx.overwrite(data, strings)
