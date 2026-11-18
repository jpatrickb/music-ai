# Scripts

Command-line entry points. Reusable logic lives in `src/music_ai/`; these wire it to files. Run from
the repo root with `uv run scripts/<name>.py` (each script's docstring has its usage). Anything
downloaded or generated goes under gitignored `data/` or `outputs/`.

## Data downloads

| Script | What it fetches |
| ------ | --------------- |
| `fetch_kern_corpus.py` | Public `**kern` score collections (Bach, Mozart, Chopin, Joplin, ...) into `data/kern/` |
| `fetch_hymns.py` | Public-domain hymn settings from the Open Hymnal Project, converted to kern into `experiments/generation/sources/hymns/` |
| `fetch_lieder.py` | Original songs from the OpenScore Lieder corpus (CC0) that Liszt transcribed for piano |
| `fetch_pdmx_liszt.py` | Selected Liszt piano scores from PDMX, converted to kern |
| `fetch_soundfont.py` | The Salamander Grand Piano SoundFont used for audio renders |

## Conversion and repair

| Script | What it does |
| ------ | ------------ |
| `musicxml_to_kern.py` | MusicXML to kern, keeping only conversions whose notes all match the source |
| `find_bad_bars.py` | Lists bars in a MusicXML file whose stored lengths don't add up |
| `beam_kern.py` | Adds beams to kern that has none (`music_ai.kern_beam`) |
| `cut_kern_excerpt.py` | Cuts a bar range out of a kern file as a standalone, valid score |

## Analysis

| Script | What it does |
| ------ | ------------ |
| `melody_map.py` | Maps where an arrangement states each phrase of the original tune (`music_ai.melody_map`) |
| `corpus_style_stats.py` | Descriptive style statistics per corpus collection, for comparison with generated pieces |
| `corpus_report.py` | Runs the notation validator over the downloaded corpus and summarizes per collection |
| `crosscheck_kern_reader.py` | Checks `music_ai.kern` against music21 on files music21 reads correctly |

## Rendering

| Script | What it does |
| ------ | ------------ |
| `render_scores.py` | Kern to PDF score, MP3 (sampled piano, with the score's dynamics and pedal) and optional score video. Needs `uv run --group render` |

## Per-experiment

Written for one experiment and kept so its results can be reproduced. They read that experiment's
samples and write to `outputs/<experiment>/` or `feedback/`.

| Script | Experiment | What it does |
| ------ | ---------- | ------------ |
| `backfill_feedback.py` | 001, 002 | Builds `feedback/` from the blind-judging page exports |
| `eval_002.py` | 002 | Validity, voice leading, playability, copying, style statistics |
| `eval_003.py` | 003 | The same plus melody fidelity |
| `record_003.py` | 003 | Records generations, then ratings and preferences, in `feedback/` |
