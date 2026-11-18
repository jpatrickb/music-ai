# music-ai

Experiments in AI for music, done in public as a learning project. Two tracks:

- **Generation** (main focus): piano arrangements and pieces written by LLMs into symbolic notation
  (Humdrum `**kern`, ABC), checked automatically and judged blind at the piano. The goal is
  musically advanced arrangements of known songs, and music for ballet classes; see
  [ROADMAP.md](ROADMAP.md). Tools are in `experiments/generation/`, results in
  `experiments/NNN-gen-*/`, and my ratings in [`feedback/`](feedback/README.md).
- **OMR**: turning images of printed scores into symbolic notation.

## OMR track

The aim is reading scores from phone photos. The approach follows the current end-to-end recipe
from the literature (Legato, Transcoda, Sheet Music Transformer): a vision encoder, an
autoregressive transformer decoder, a text encoding of the score, and grammar-constrained decoding
so outputs are always valid.

Each stage is a milestone, trained and evaluated before moving on:

1. **Camera-PrIMuS**: monophonic single-staff incipits with simulated camera distortion. A laptop-trainable baseline.
2. **GrandStaff**: polyphonic two-staff piano scores.
3. **Rendered OpenScore Lieder**: voice + piano with lyrics, rendered synthetically at scale.
4. **Real-world photos**: fine-tune and evaluate on photographed and scanned scores of all kinds (piano, vocal, ensemble), compared against Audiveris.

Evaluation uses established metrics (OMR-NED from the Sheet Music Benchmark, plus CER) rather than invented ones.

## Layout

```
src/music_ai/   reusable code: kern reader, style statistics, feedback data; OMR models and eval
experiments/   one folder per experiment (NNN-slug/) with its README and results;
               experiments/generation/ holds the generation context docs and checkers
feedback/      my ratings and preferences on generated music (JSONL)
configs/       training/eval configs
scripts/       one-off utilities (downloads, rendering, conversion)
tests/         pytest tests
data/          datasets and renders (gitignored)
```

## Setup

Requires [uv](https://docs.astral.sh/uv/).

```sh
uv sync
uv run pytest
```

## Status

- Generation: experiments 001–002 done; next is Christmas hymn arrangements (ROADMAP stage 1).
- OMR: Phase 0, environment setup and a reproducible PrIMuS-scale baseline.
