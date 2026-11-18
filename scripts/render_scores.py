"""Render `**kern` samples to a PDF score and an MP3 (and optionally a score video), so they can
be read and heard on GitHub without any music software.

Beams are added first (music_ai.kern_beam), as on the judging pages; notes are unchanged.
Verovio engraves the SVG pages and writes the MIDI. Verovio's MIDI ignores dynamics, so each
note's velocity is set from the score's `**dynam` markings and hairpins (music_ai.dynamics) before
the MIDI is written; a piece without dynamics plays at `--velocity` (default 90). Then:

- `rsvg-convert` (librsvg, `brew install librsvg`): SVG pages -> one PDF (and PNGs for video)
- `tinysoundfont` (dev dependency): MIDI -> audio through a piano SoundFont, preset 0 forced on
  every channel. The default is the Salamander Grand Piano (a sampled Yamaha C5, CC BY 3.0),
  fetched by `scripts/fetch_soundfont.py`; override with `--soundfont`. It has 16 velocity
  layers, so louder dynamics also sound brighter. The score's pedal marks are applied by holding
  note-offs while the pedal is down, since TinySoundFont ignores the sustain controller.
- `ffmpeg`: MP3 at -16 LUFS overall (EBU R128), by one fixed gain plus a peak limiter, so the
  difference between soft and loud passages is kept

Writes `<name>.pdf` and `<name>.mp3` into the experiment's `renders/` folder
(or `--out`), where `<name>` keeps the arm folder, e.g. `samples/B/T1-1.krn` -> `B-T1-1`. The MIDI,
with its velocities, goes to `outputs/midi/<name>.mid` (gitignored) for use in other software.

With `--video`, also writes `outputs/videos/<name>.mp4`: the score pages, each shown from its
first note's time, over the audio. GitHub won't play audio in a README, but a video uploaded
through the web editor (a `github.com/user-attachments/...` link on its own line) plays inline.
The videos are gitignored since they repeat the PDF and MP3.

Usage:
    uv run scripts/render_scores.py experiments/003-gen-hymn-arrangements/samples/H4-2.krn
"""

from __future__ import annotations

import argparse
import base64
import bisect
import os
import re
import shutil
import subprocess
import sys
import tempfile
import wave
from pathlib import Path

import numpy as np
import tinysoundfont
import verovio

from music_ai.dynamics import dynamic_marks, velocity_curve
from music_ai.kern_beam import add_beams

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fetch_soundfont import SF2 as DEFAULT_SOUNDFONT

ROOT = Path(__file__).resolve().parents[1]
SAMPLE_RATE = 44100
TAIL_SECONDS = 2.5  # let the last chord ring out
TARGET_LUFS = -16.0  # a typical streaming level
LIMIT = 0.84  # peak ceiling after gain, about -1.5 dBFS

# Letter-ish pages at a readable size; Verovio units are tenths of a mm.
VEROVIO_OPTIONS = {
    "inputFrom": "humdrum",
    "pageWidth": 2159,
    "pageHeight": 2794,
    "pageMarginTop": 100,
    "pageMarginBottom": 100,
    "pageMarginLeft": 100,
    "pageMarginRight": 100,
    "scale": 40,
    "footer": "none",
}


def find_tool(name: str) -> str:
    path = shutil.which(name)
    if not path:
        raise SystemExit(f"not found on PATH: {name}")
    return path


def experiment_dir(sample: Path) -> Path:
    """The `experiments/NNN-slug/` folder a sample lives under."""
    for parent in sample.resolve().parents:
        if parent.parent.name == "experiments":
            return parent
    raise SystemExit(f"{sample} is not under experiments/NNN-slug/")


def output_stem(sample: Path) -> str:
    """`samples/B/T1-1.krn` -> `B-T1-1`; `samples/H4-2.krn` -> `H4-2` (keeps the arm in the name)."""
    parent = sample.parent.name
    return sample.stem if parent == "samples" else f"{parent}-{sample.stem}"


def page_start_times(tk: verovio.toolkit) -> list[float]:
    """Seconds at which each page's first note sounds, from Verovio's timemap (page 1 at 0)."""
    starts: dict[int, float] = {1: 0.0}
    for event in tk.renderToTimemap():
        for note_id in event.get("on", []):
            starts.setdefault(tk.getPageWithElement(note_id), event["tstamp"] / 1000)
    return [starts[n] for n in range(1, tk.getPageCount() + 1)]


_LINE = re.compile(r"-L(\d+)F")  # Verovio ids from Humdrum carry the source line: note-L14F1


def note_velocities(text: str, tk: verovio.toolkit, fallback: int) -> dict[str, int]:
    """MIDI velocity for every sounding note id, from the `**dynam` spines of `text`.

    A marking takes effect at the first note on or after its line; each note then gets the curve's
    value at its onset time.
    """
    onsets: dict[str, float] = {}
    for event in tk.renderToTimemap():
        for note_id in event.get("on", []):
            onsets.setdefault(note_id, event["tstamp"] / 1000)
    marks = dynamic_marks(text)
    if not marks:
        return {note_id: fallback for note_id in onsets}
    by_line = sorted(
        (int(m.group(1)), t) for note_id, t in onsets.items() if (m := _LINE.search(note_id))
    )
    lines = [line for line, _ in by_line]
    timed = []
    for mark in marks:
        i = bisect.bisect_left(lines, mark.line)
        if i < len(by_line):
            timed.append((by_line[i][1], mark.token))
    curve = velocity_curve(timed)
    return {note_id: curve(t) for note_id, t in onsets.items()}


def midi_with_velocities(tk: verovio.toolkit, velocities: dict[str, int]) -> bytes:
    """Verovio's MIDI with each note's MEI `@vel` set (Verovio's MIDI export honours it)."""
    mei = tk.getMEI()
    mei = re.sub(
        r'<note (?=[^>]*xml:id="([^"]+)")',
        lambda m: f'<note vel="{velocities[m.group(1)]}" ' if m.group(1) in velocities else m[0],
        mei,
    )
    mei_tk = verovio.toolkit()
    mei_tk.setOptions({**VEROVIO_OPTIONS, "inputFrom": "mei"})
    if not mei_tk.loadData(mei):
        raise SystemExit("verovio could not reload its own MEI")
    return base64.b64decode(mei_tk.renderToMIDI())


def apply_sustain(events: list[tinysoundfont.midi.Event]) -> list[tinysoundfont.midi.Event]:
    """Hold note-offs while the sustain pedal (CC 64) is down, releasing them when it lifts.

    TinySoundFont ignores CC 64, so without this the score's pedal markings would do nothing.
    A key struck again while held is released just before the new attack.
    """
    midi = tinysoundfont.midi
    out: list[midi.Event] = []
    down: dict[int, bool] = {}
    held: dict[int, set[int]] = {}

    def release(ch: int, keys: set[int], t: float) -> None:
        out.extend(midi.Event(action=midi.NoteOff(key), t=t, channel=ch) for key in sorted(keys))
        keys.clear()

    for e in sorted(events, key=lambda e: e.t):  # stable: keeps the file's order within a time
        a, ch = e.action, e.channel
        keys = held.setdefault(ch, set())
        if isinstance(a, midi.ControlChange) and a.control == 64:
            down[ch] = a.control_value >= 64
            if not down[ch]:
                release(ch, keys, e.t)
        elif isinstance(a, midi.NoteOff) or (isinstance(a, midi.NoteOn) and a.velocity == 0):
            if down.get(ch):
                keys.add(a.key)
                continue
        elif isinstance(a, midi.NoteOn) and a.key in keys:
            keys.discard(a.key)
            out.append(midi.Event(action=midi.NoteOff(a.key), t=e.t, channel=ch))
        out.append(e)
    end = out[-1].t if out else 0.0
    for ch, keys in held.items():
        release(ch, keys, end)
    return out


def synthesize_piano(midi: Path, seconds: float, soundfont: Path, wav: Path) -> None:
    """Play `midi` through the SoundFont's preset 0 (the piano) on every channel.
    Peak-normalized here; loudness is set when encoding."""
    synth = tinysoundfont.Synth(samplerate=SAMPLE_RATE)
    sf = synth.sfload(str(soundfont))
    for channel in range(16):
        synth.program_select(channel, sf, 0, 0)
    sequencer = tinysoundfont.Sequencer(synth)
    # The MIDI's own program changes would apply too; Verovio writes none for plain kern.
    sequencer.add(apply_sustain(tinysoundfont.midi.load(str(midi))))
    frames = int(seconds * SAMPLE_RATE)
    audio = np.frombuffer(synth.generate(frames), dtype=np.float32).reshape(-1, 2)
    peak = float(np.abs(audio).max()) or 1.0
    pcm = (audio / peak * 0.99 * 32767).astype(np.int16)
    with wave.open(str(wav), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SAMPLE_RATE)
        w.writeframes(pcm.tobytes())


def encode_mp3(wav: Path, mp3: Path, ffmpeg: str) -> None:
    """Measure integrated loudness, then apply one gain to reach TARGET_LUFS (no compression)."""
    probe = subprocess.run(
        [ffmpeg, "-hide_banner", "-i", str(wav), "-af", "ebur128", "-f", "null", "-"],
        check=True,
        capture_output=True,
        text=True,
    )
    integrated = float(re.findall(r"I:\s+(-?[\d.]+) LUFS", probe.stderr)[-1])
    gain = TARGET_LUFS - integrated
    af = f"volume={gain:.2f}dB,alimiter=limit={LIMIT}:level=disabled"
    subprocess.run(
        [ffmpeg, "-y", "-loglevel", "error", "-i", str(wav), "-af", af, "-b:a", "192k", str(mp3)],
        check=True,
    )


def score_video(
    pngs: list[Path], starts: list[float], total: float, mp3: Path, mp4: Path, ffmpeg: str
) -> None:
    """A still-image video: page n from starts[n] until the next page, the last until the end."""
    durations = [b - a for a, b in zip(starts, starts[1:] + [total])]
    inputs: list[str] = []
    for png, seconds in zip(pngs, durations, strict=True):
        inputs += ["-loop", "1", "-framerate", "5", "-t", f"{seconds:.3f}", "-i", str(png)]
    n = len(pngs)
    graph = (
        "".join(f"[{i}:v]scale=1200:-2,format=yuv420p,setsar=1[v{i}];" for i in range(n))
        + "".join(f"[v{i}]" for i in range(n))
        + f"concat=n={n}:v=1:a=0[v]"
    )
    # fmt: off
    subprocess.run(
        [ffmpeg, "-y", "-loglevel", "error", *inputs, "-i", str(mp3),
         "-filter_complex", graph, "-map", "[v]", "-map", f"{n}:a",
         "-c:v", "libx264", "-tune", "stillimage", "-r", "5",
         "-c:a", "aac", "-b:a", "160k", "-t", f"{total:.3f}", str(mp4)],
        check=True,
    )
    # fmt: on


def render(
    sample: Path,
    out_dir: Path,
    rsvg: str,
    ffmpeg: str,
    soundfont: Path,
    velocity: int,
    video_dir: Path | None,
) -> list[Path]:
    verovio.enableLog(
        verovio.LOG_ERROR
    )  # layout notices are noise here; validate_notation checks scores
    tk = verovio.toolkit()
    tk.setOptions(VEROVIO_OPTIONS)
    text = add_beams(sample.read_text())
    if not tk.loadData(text):
        raise SystemExit(f"verovio could not load {sample}")

    out_dir.mkdir(parents=True, exist_ok=True)
    stem = output_stem(sample)
    pdf, mp3 = out_dir / f"{stem}.pdf", out_dir / f"{stem}.mp3"
    written = [pdf, mp3]
    # A fixed date keeps re-rendered PDFs byte-identical when the music hasn't changed.
    env = {**os.environ, "SOURCE_DATE_EPOCH": "0"}

    with tempfile.TemporaryDirectory() as tmp:
        pages = []
        for n in range(1, tk.getPageCount() + 1):
            page = Path(tmp) / f"page{n:02d}.svg"
            page.write_text(tk.renderToSVG(n))
            pages.append(page)
        subprocess.run([rsvg, "-f", "pdf", "-o", str(pdf), *map(str, pages)], check=True, env=env)

        midi = ROOT / "outputs" / "midi" / f"{stem}.mid"
        midi.parent.mkdir(parents=True, exist_ok=True)
        midi.write_bytes(midi_with_velocities(tk, note_velocities(text, tk, velocity)))
        total = tk.renderToTimemap()[-1]["tstamp"] / 1000 + TAIL_SECONDS
        wav = Path(tmp) / f"{stem}.wav"
        synthesize_piano(midi, total, soundfont, wav)
        encode_mp3(wav, mp3, ffmpeg)

        if video_dir:
            pngs = [page.with_suffix(".png") for page in pages]
            for page, page_png in zip(pages, pngs, strict=True):
                subprocess.run(
                    [
                        rsvg,
                        "-f",
                        "png",
                        "-w",
                        "1200",
                        "-b",
                        "white",
                        "-o",
                        str(page_png),
                        str(page),
                    ],
                    check=True,
                )
            video_dir.mkdir(parents=True, exist_ok=True)
            mp4 = video_dir / f"{stem}.mp4"
            score_video(pngs, page_start_times(tk), total, mp3, mp4, ffmpeg)
            written.append(mp4)

    return written


def main() -> None:
    ap = argparse.ArgumentParser(description="Render kern samples to a PDF score and an MP3.")
    ap.add_argument("samples", nargs="+", type=Path, help="kern files under experiments/")
    ap.add_argument("--out", type=Path, help="output folder (default: <experiment>/renders/)")
    ap.add_argument("--video", action="store_true", help="also write outputs/videos/<name>.mp4")
    ap.add_argument("--soundfont", type=Path, default=DEFAULT_SOUNDFONT, help="sf2/sf3 file")
    ap.add_argument("--velocity", type=int, default=90, help="velocity if a piece has no dynamics")
    args = ap.parse_args()

    if not args.soundfont.exists():
        raise SystemExit(f"SoundFont not found: {args.soundfont} (run scripts/fetch_soundfont.py)")
    rsvg, ffmpeg = find_tool("rsvg-convert"), find_tool("ffmpeg")
    video_dir = ROOT / "outputs" / "videos" if args.video else None
    for sample in args.samples:
        out_dir = args.out or experiment_dir(sample) / "renders"
        for path in render(sample, out_dir, rsvg, ffmpeg, args.soundfont, args.velocity, video_dir):
            print(path)


if __name__ == "__main__":
    main()
