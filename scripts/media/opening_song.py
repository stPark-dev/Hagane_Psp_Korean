"""Personal build only: put your own song under the opening movie (DAT001.cpk entry 00058).

    python3 scripts/media/opening_song.py SONG SRC_DAT001.cpk OUT_DAT001.cpk \
        [--start SEC] [--fade-in SEC] [--fade SEC] [--end SEC] [--encoder PATH]

The song is never stored in the repository or the distributed patch: it is read from SONG at
build time, taken from --start, faded in over --fade-in seconds and out over the --fade seconds
before --end (seconds into the movie; default 80.5, where the game's own song has ended: the
last 2.6 s of the 83.1-s movie are its tail, and audio that lags in playback is cut there),
padded with silence to the movie's 1790 ATRAC3plus frames, encoded to ATRAC3plus with atracdenc built for 744-byte frames
(the movie's frame size; see docs/handoff.md), and written over the old frames in place.
"""
import argparse
import os
import subprocess
import sys
import tempfile

sys.path.insert(0, ".")
from tools import cpk, pmf  # noqa: E402

OPENING, RATE, BLOCK = "00058", 44100, 2048


def encode(song, start, fade_in, fade, end, frames, size, encoder, tmp):
    end = min(end, frames * BLOCK / RATE)
    wav, raw = os.path.join(tmp, "song.wav"), os.path.join(tmp, "song.at3p")
    fades = (f"afade=t=in:st=0:d={fade_in}," if fade_in else "") + f"afade=t=out:st={end - fade:.3f}:d={fade}"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(start), "-t", f"{end:.6f}", "-i", song,
                    "-af", f"{fades},apad=whole_len={frames * BLOCK}",
                    "-ar", str(RATE), "-ac", "2", "-c:a", "pcm_s16le", wav], check=True)
    subprocess.run([encoder, "-e", "atrac3plus", "--container", "raw", "--nostdout", "-i", wav, "-o", raw],
                   check=True)
    data = open(raw, "rb").read()
    if len(data) % size:
        raise SystemExit(f"encoder wrote {len(data)} bytes, not whole {size}-byte frames: "
                         f"build atracdenc with BitStream(out, {size}) (docs/handoff.md)")
    out = [data[k:k + size] for k in range(0, len(data), size)]
    if len(out) < frames:
        raise SystemExit(f"encoder wrote {len(out)} frames, the movie needs {frames}")
    return out[:frames]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("song")
    ap.add_argument("src")
    ap.add_argument("out")
    ap.add_argument("--start", type=float, default=0.0)
    ap.add_argument("--fade-in", type=float, default=0.0)
    ap.add_argument("--fade", type=float, default=3.0)
    ap.add_argument("--end", type=float, default=80.5)
    ap.add_argument("--encoder", default="work/ext/atracdenc/build/src/atracdenc")
    a = ap.parse_args()
    arc = cpk.CpkArchive(a.src)
    movie = arc.read(arc.by_path()[OPENING])
    old = pmf.audio_frames(movie)
    with tempfile.TemporaryDirectory() as tmp:
        new = encode(a.song, a.start, a.fade_in, a.fade, a.end, len(old), len(old[0]), a.encoder, tmp)
    cpk.overwrite_same_size(a.src, a.out, {OPENING: pmf.replace_audio(movie, new)})
    print(f"{a.out}: opening audio replaced ({len(new)} frames of {len(new[0])} bytes)")


if __name__ == "__main__":
    main()
