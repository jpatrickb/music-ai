# 002: LLM generation with real-composer excerpts in context (draft, not yet run)

## Question / hypothesis

Does adding a few short excerpts of real music in the target style to the generator's context make
its piano pieces more idiomatic than the theory docs alone?

Hypothesis: yes. Pilot 001 showed the generators copy whatever the context shows (the cadential 6/4
voicing, the root-position rule in `theory/01`), and the owner judged the output correct but
textbook-bland. Real excerpts should move inversion use, non-chord tones and textures toward the
composers', measured by the style statistics below and by blind judging.

## Setup (planned)

- **Arms:** (A) theory/style docs only; (B) the same docs plus 2–3 short excerpts (8–16 bars) by
  real composers matching the task's style. Excerpts are cut at run time from the kern corpus in
  `data/kern/` and referenced here by file and bar range only (the encodings are licensed
  separately; see `scripts/fetch_kern_corpus.py`).
- **Format:** `**kern` only (the corpus is kern). ABC vs kern is set aside as a later side test.
- **Tasks:** about four harder briefs in styles the corpus covers: a Chopin-style prelude or
  mazurka, a Mozart-style sonata exposition, a Bach-style two-part invention, a Joplin rag. 3
  samples per task per arm.
- **Before running:** drop the root-position rule from `theory/01`; add automatic checks for hand
  span, leap size, cross relations and hand crossing; add an n-gram copy check against the excerpts.
- **Evaluation:** validator and harmony checker as in 001; style statistics compared with the
  matching composer collection; blind owner judging at the piano (same scorecard as 001).
- **Generator:** to decide (teammates as in 001, or a scripted API / open-weights run with a fixed
  prompt).

## Baseline: corpus style statistics

Computed by `scripts/corpus_style_stats.py` (`omr_lab.style_stats` on `omr_lab.kern`) from commit
`0614e2c` plus uncommitted changes: the 12 pinned corpus collections and the 8 pilot-001 samples.
Medians over pieces.

| Collection         |   n | Root | 1st inv | 2nd inv | 7th | Chord change | NCT weight | Melody NCT | RH span p95 | LH leap p50 / p95 | Melody steps | RH chords |
| ------------------ | --: | ---: | ------: | ------: | --: | -----------: | ---------: | ---------: | ----------: | ----------------: | -----------: | --------: |
| Bach chorales      | 370 |  55% |     23% |      7% | 43% |          85% |         6% |          – |           – |                 – |            – |         – |
| Bach WTC           |  96 |  36% |     21% |     18% | 69% |          91% |        13% |        23% |      16 (a) |            2 / 11 |          57% |        0% |
| Bach inventions    |  30 |  36% |     20% |     16% | 61% |          92% |        14% |        21% |           8 |            2 / 10 |          63% |        0% |
| Scarlatti          |  65 |  44% |     22% |     19% | 41% |          86% |         8% |        17% |          10 |            2 / 12 |          55% |        0% |
| Haydn sonatas      |  25 |  42% |     26% |     19% | 47% |          85% |         8% |        18% |          10 |            3 / 12 |          50% |        0% |
| Mozart sonatas     |  69 |  38% |     25% |     20% | 54% |          83% |        10% |        19% |          12 |            3 / 12 |          55% |        1% |
| Beethoven sonatas  | 103 |  41% |     22% |     19% | 50% |          75% |         7% |        14% |          12 |            4 / 12 |          41% |        7% |
| Hummel preludes    |  24 |  41% |     23% |     15% | 57% |          75% |         6% |        15% |           9 |            3 / 12 |          29% |        3% |
| Chopin preludes    |  24 |  43% |     20% |     16% | 52% |          78% |         8% |        11% |          12 |            7 / 16 |          24% |        7% |
| Chopin mazurkas    |  52 |  49% |     15% |     17% | 50% |          74% |         7% |        18% |          12 |            5 / 16 |          56% |        3% |
| Scriabin           | 207 |  36% |     18% |     19% | 64% |          78% |        11% |        22% |          12 |            6 / 19 |          40% |       14% |
| Joplin             |  47 |  42% |     18% |     22% | 60% |          73% |         8% |        20% |          12 |            5 / 16 |          48% |       19% |
| **Pilot 001 kern** |   4 |  86% |      3% |      9% | 17% |          60% |         0% |         1% |          11 |          5 / 15.5 |          53% |       56% |
| **Pilot 001 ABC**  |   4 |  71% |      9% |     15% | 12% |          63% |         1% |         5% |          11 |            5 / 13 |          58% |       51% |

Percentages are of harmonized beats (inversions, 7th, chord change), of sounding duration (NCT
weight), of melody notes (melody NCT, steps) or of RH attacks (RH chords). Spans and leaps are in
semitones.

What it shows, and how it matches the owner's 001 judging:

- **Root position:** pilot 71–86% vs 36–55% for every composer. This is the "everything in root
  position" complaint, now measured.
- **Non-chord tones:** pilot 0–1% of sounding weight vs 6–14%, and 1–5% of melody notes vs 11–23%.
  This is the "needs more non-chord tones" complaint.
- **Seventh chords** 12–17% vs 41–69%, and **block RH chords** 51–56% of attacks vs 0–19%: the pilot
  writes chorale-like block chords where composers write melody and figuration.
- Per piece, the stats also catch the specific playability notes: kern T3's final RH chord spans 20
  semitones (E4–C6) and its LH leaps reach 24 semitones; ABC T3, the one preferred for its flowing
  melody, has 12% melody NCTs vs 2% in kern T3.

Caveats:

- Harmony comes from chord-template fitting per beat, an estimate. Passing tones that happen to
  complete a seventh chord count as sevenths, so the 7th rates are inflated for all rows alike.
  Compare rows, don't read the numbers as analyses.
- (a) Hand statistics treat each staff as a hand. That holds for homophonic piano writing, but in
  fugues the encodings put each voice on a fixed staff while the middle voices actually move between
  the hands, so the WTC hand-span figures are not meaningful.
- The pilot rows are 4 pieces each; the composer rows are whole collections.
