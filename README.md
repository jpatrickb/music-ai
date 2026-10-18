# omr-lab

Experiments in **optical music recognition (OMR)**: turning images of printed scores into symbolic notation (ABC / Humdrum `**kern`), with the long-term aim of reading scores from phone photos.

The approach follows the current end-to-end recipe from the literature (Legato, Transcoda, Sheet Music Transformer): a vision encoder, an autoregressive transformer decoder, a text encoding of the score, and grammar-constrained decoding so outputs are always valid.

## Roadmap

Each stage is a milestone, trained and evaluated before moving on:

1. **Camera-PrIMuS**: monophonic single-staff incipits with simulated camera distortion. A laptop-trainable baseline.
2. **GrandStaff**: polyphonic two-staff piano scores.
3. **Rendered OpenScore Lieder**: voice + piano with lyrics, rendered synthetically at scale.
4. **Real-world photos**: fine-tune and evaluate on photographed and scanned scores of all kinds (piano, vocal, ensemble), compared against Audiveris.

Evaluation uses established metrics (OMR-NED from the Sheet Music Benchmark, plus CER) rather than invented ones.

## Layout

```
src/omr_lab/   reusable code: data loading, tokenizers, models, decoding, eval
experiments/   one folder per experiment (NNN-slug/) with its README and results
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

Phase 0: environment setup and a reproducible PrIMuS-scale baseline.
