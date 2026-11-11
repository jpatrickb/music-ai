# 003: Advanced piano arrangements of Christmas hymns

## Question / hypothesis

Roadmap stage 1: can the current setup produce an advanced solo-piano hymn arrangement the owner
would actually play this December? And what fails: the tune, the texture, the harmony, the form,
playability, or notation?

No arms: one condition with everything 001–002 suggested (theory docs, real piano excerpts as
texture models, the corrected kern reference), plus a new arranging guide. The point is a
capability probe and the first arrangement data for `feedback/`, not a comparison.

## Setup

- **Tunes (H1–H5):** O Come, All Ye Faithful; Hark! The Herald Angels Sing; Joy to the World;
  Silent Night; The First Noel. Four-part hymnal settings from the Open Hymnal Project (public
  domain), converted to kern by `scripts/fetch_hymns.py` into
  `experiments/generation/sources/hymns/`.
- **Brief:** an introduction, at least two complete statements of the tune (the second varied),
  an optional key change, an ending; about 2–3 minutes; advanced amateur level; tune recognisable
  and mostly on top. Exact prompt in [`prompt.md`](prompt.md).
- **Context:** kern reference, `arranging/01-hymn-arrangement.md` (new), theory 01–05, styles/01,
  the hymn source, and two Chopin excerpts as texture models (Op. 28 No. 17 and No. 13, bars
  1–12 each, cut at run time into `data/excerpts/003/`).
- **Generator:** Claude Code teammate agents (subscription), model `claude-opus-5-5`, one fresh
  agent per piece, no code execution. 2 samples per tune, 10 pieces.
- **Evaluation:**
  - validator (now including the pitch-spelling check), harmony checker, playability check;
  - melody fidelity (`music_ai.melody_fidelity`): statements of the tune found, with transposition,
    coverage and top coverage; thresholds provisional, calibrated against chance on the 002 pieces;
  - blind owner judging at the piano, with automatic beaming (`music_ai.kern_beam`) applied to the
    renders;
  - results recorded in `feedback/`.
- **Code and context:** run 2026-11-10 from `70af713` plus uncommitted changes: the `music_ai`
  package rename, `kern_beam`, `melody_fidelity`, `fetch_hymns.py`, the arranging guide and this
  folder.

## Results

Generated pieces: `samples/H{n}-{k}.krn`. Evaluation: `uv run scripts/eval_003.py` (per-sample
JSON in `outputs/003-gen-hymn-arrangements/`). Recorded in `feedback/` by
`scripts/record_003.py`.

### Automatic checks

| Piece | Bars | Length | Statements of the tune (bar, key change, coverage / on top) | Notes |
| ----- | ---: | -----: | ------------------------------------------------------------ | ----- |
| H1-1  |   50 |   2:38 | b5, b27 up 2 (99% / 99% each)                                | 2 statements |
| H1-2  |   51 |   2:41 | b4, b27 up 1 (100%)                                          | 2 statements |
| H2-1  |   52 |   2:36 | b5, b27 up 2 (100%)                                          | 2 statements |
| H2-2  |   54 |   2:34 | b7, b29 up 2 (100%)                                          | 2 statements |
| H3-1  |   78 |   2:22 | b9, b29, b52 up 1 (97–100%)                                  | |
| H3-2  |   79 |   2:12 | b9, b30, b52 up 1 (100%)                                     | |
| H4-1  |   52 |   2:10 | b7, b21, b35 up 2 (100%)                                     | |
| H4-2  |   50 |   2:05 | b7, b19, b32 up 2 (100%)                                     | 2 outer-voice parallel 5ths |
| H5-1  |   88 |   2:52 | b6, b31, b57 up 1 (99–100%)                                  | LH block-chord tenths (8 bars) |
| H5-2  |   61 |   2:24 | b5, b31 up 1 (100%)                                          | 2 statements |

- **Validity: 10/10** valid on the first try, including the new pitch-spelling check. All within
  the 2–3 minute target.
- **The tune is kept almost literally.** Every statement the agents described was found, at
  97–100% coverage, always on top: no arrangement moves the tune to an inner voice or varies its
  rhythm. Faithful, but possibly too literal for "advanced".
- **Playability:** one real problem: H5-1 writes left-hand block chords spanning a tenth (e.g.
  G2–D3–B3 struck together, 8 bars), against the brief's ninth limit. No other high findings.
- **Voice leading:** the harmony checker reports 6–15 high-severity findings per piece (107 in
  all), but it was built for block-chord voice leading. 54 are octave doublings (melody or bass
  in octaves, a deliberate texture) and most of the rest are parallel 5ths between "voices" the
  checker infers inside broken-chord figures, which isn't reliable. Only 2 are 5ths between the
  outer voices (H4-2, bars 14 and 38), plausibly real slips. Treat these counts as noise here.
- **Copying:** no flags against the Chopin texture excerpts.
- **Strong convergence on one plan** (from the agents' own descriptions, confirmed by the
  statement bars):
  - all 10 open with an introduction over a pedal or drone, built from the tune's first or last
    phrase;
  - all 10 change key for the last statement: the five whole-step changes all use a pivot chord
    that is iii of the old key and ii of the new (e.g. A minor from F to G in both Hark!
    arrangements); of the five half-step changes, three use a chord that is iv of the old key and
    iii of the new (C minor or G minor) and two a common-tone shift;
  - all 10 have a deceptive cadence near the end (9 onto ♭VI, 1 onto vi), then a quiet plagal
    tag over a tonic pedal.

  The plan follows the arranging guide's suggested form closely, so the guide likely drives it.

### Owner judging

Pending (private page; two arrangements per hymn in a random order, seed 20261111; difficulty
and "would you play it?" recorded alongside the 1–5 scores).
