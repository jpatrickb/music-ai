# 002: LLM generation with real-composer excerpts in context

## Question / hypothesis

Does adding a few short excerpts of real music in the target style to the generator's context make
its piano pieces more idiomatic than the theory docs alone?

Hypothesis: yes. Pilot 001 showed the generators copy whatever the context shows (the cadential 6/4
voicing, the root-position rule in `theory/01`), and the owner judged the output correct but
textbook-bland. Real excerpts should move inversion use, non-chord tones and textures toward the
composers', measured by the style statistics below and by blind judging.

## Setup

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
- **Generator:** Claude Code teammate agents (subscription), model `claude-opus-5-5`, one fresh
  agent per piece, no code execution (as in 001). The exact prompt and briefs are in
  [`prompt.md`](prompt.md). Arms differ only in the excerpt paragraph.
- **Code and context:** run 2026-11-10 from `d42233b` plus uncommitted changes: `theory/01` without
  the root-position rule, the `omr_lab.kern` grace-line fix, `hands()` by staff number,
  `playability_check.py`, `scripts/cut_kern_excerpt.py`, `scripts/eval_002.py`.
- **Not controlled:** the prompt now asks for no stretches beyond a ninth (both arms), and
  `theory/01` changed since 001, so 002 is not comparable to 001 except descriptively.

## Results

Generated pieces: `samples/{A,B}/T{n}-{k}.krn` (A = docs only, B = docs + excerpts). Evaluation:
`uv run scripts/eval_002.py` (per-sample JSON in `outputs/002-gen-real-excerpts/`).

### Automatic checks

- **Validity: 22/24 correct as generated.** All 24 passed the validator at first, but two had
  misspelled pitches it did not catch: A-T1-3 (2 notes) and B-T2-2 (40 notes) wrote F#5 as `f#f#`
  instead of `ff#` (also `g#g#`, `cc#cc#`). Verovio renders and plays these as double sharps in the
  wrong octave, and `omr_lab.kern` silently read the first pitch only, so the checkers analysed
  F#4. The owner caught it at the piano. After judging, the two files were corrected mechanically
  (`f#f#`→`ff#`, `g#g#`→`gg#`, `cc#cc#`→`ccc#`; octave confirmed by stepwise context), the reader
  now warns and the validator errors on such tokens (`malformed_pitch`), and the kern reference
  states the rule. On the 1,112 corpus files the new check flags 7 tokens, all real encoding slips
  (chord notes missing their separating space).
- **Voice leading and playability (after the fix):** no piece has high-severity harmony or
  playability findings. B-T2-2's earlier 5 high-severity findings and 15-semitone RH chord were
  artifacts of the misspelling.
- **Copying:** checked against each task's excerpts, with the composer's other pieces as background
  (shared runs also found there count as common figuration). Arm A never saw the excerpts, so it is
  the control: it still produced chance matches (A-T3-2 flagged high against the Bach inventions,
  whose subjects are built from scale fragments). Two arm-B Mozart pieces (B-T2-1, B-T2-2) share 3–5
  distinctive runs (up to 13 notes) with the K. 545 opening's Alberti bass and harmonic rhythm, more
  than any arm-A piece: the excerpts leak into the output there. The flag threshold (3+ runs or 12+
  notes) was set from arm A in this same run, so it still needs checking on a fresh run.
- **Convergence:** within a task, pieces from both arms share much of the same plan (going by the
  agents' own descriptions of their pieces). All six T1 preludes cadence in B♭ midway and use a
  Neapolitan before the end; four open on a sighing D–E♭ motive and four over a chromatic bass
  falling from G. All six T2 expositions are 30–32 bars of mostly 8-bar sections, pivoting through B
  minor or F♯ minor. Three rags (one in arm A, two in arm B) are even titled "Linden Street Rag",
  and two arm-A rags "Riverboat Rag". The excerpts did not change the large-scale plan the model
  reaches for.
- **Descriptive statistics** (medians per task, arm A vs B; descriptions, not quality): root
  position T1 43% vs 63%, T2 44% vs 52%, T3 47% vs 59%, T4 46% vs 49%; melody NCTs T1 10% vs 16%, T2
  16% vs 11%, T3 20% vs 14%, T4 6% vs 10%. Both arms are now inside the composers' root-position
  range (36–55%) or near it, unlike 001 (71–86%); the `theory/01` change, not the excerpts, is the
  likely cause. Arm B is, if anything, _more_ root-position.

### Blind piano judging

The owner rated all 24 at the piano on a private page: six pieces per task in a random order (seed
20261110), titles and analysis spines removed, arm hidden. Scores 1–5 for fit to the brief,
musicality and playability, a written note on each, and a favourite per task. A-T1-3 and B-T2-2
were heard as rendered, with the misspelled sharps.

| Task              | Brief A / B | Musicality A / B | Playability A / B | Favourite |
| ----------------- | ----------: | ---------------: | ----------------: | --------- |
| T1 Chopin prelude |   4.0 / 5.0 |        3.3 / 5.0 |         4.7 / 5.0 | B-T1-1    |
| T2 Mozart expo.   |   4.7 / 5.0 |        4.0 / 5.0 |         4.7 / 5.0 | B-T2-1    |
| T3 Bach invention |   4.3 / 5.0 |        3.7 / 4.7 |         4.7 / 5.0 | A-T3-2    |
| T4 Joplin rag     |   5.0 / 5.0 |        4.7 / 5.0 |         5.0 / 5.0 | B-T4-3    |
| **All**           |   4.5 / 5.0 |        3.9 / 4.9 |         4.8 / 5.0 | 3 of 4 B  |

Means of 3 pieces per cell. 11 of 12 arm-B pieces got musicality 5 vs 3 of 12 in arm A; arm B
scored at least as well as arm A in every task. A within-task permutation test of the musicality
difference (1.0 point) gives p ≈ 0.001. That is one rater, 24 pieces and scores near the ceiling,
so it supports "excerpts helped in this run", not a size of effect. Arm positions on the page were
balanced (mean slot 3.4 A vs 3.6 B), so rating drift through the page does not explain it.

What the notes say:

- **Arm B** is praised for sequence and repetition that serves the piece, one motif carried
  through (B-T3-2), harmonic progressions that feel idiomatic (Chopin-like in T1, natural switching
  between major and minor and secondary dominants in T3), and varied bass patterns in the Mozart
  (Alberti, octaves, chords, mixed rhythms).
- **Arm A** has the weakest pieces: two inventions "like someone improvising over a chord
  progression in the style of Bach" (A-T3-1, with a melodic tritone; A-T3-3), close-clustered LH
  arpeggios in A-T1-2, and odd harmony in the Mozart transitions (A-T2-1, A-T2-2, A-T2-3, around
  bars 9–14). But the favourite invention, A-T3-2, is arm A.
- **Both arms:** the Chopin LH rhythm is too uniform; rag syncopation sometimes sits wrong
  (phrase ends on a sixteenth off-beat; one rhythm repeated bar after bar); A-T4-1's strains are
  unequal; A-T4-2 ends on a I6/4 where a V was needed. The Chopin and Mozart pieces are simpler than
  the owner wants to play; the inventions and some rags would take practice.
- **Notation (whole batch):** no beams: every eighth and sixteenth has its own flag, because the
  generated kern has no `L`/`J` beam markers and Verovio does not beam kern automatically. This
  must be fixed before anything is meant for a pianist. Plus the double sharps above.

Arm B was _more_ root-position than arm A (see the descriptive statistics) and still rated higher,
another reminder that the corpus statistics describe and do not measure quality.

Blind key (page slot → sample): T1 1=A1 2=B2 3=B3 4=B1 5=A2 6=A3; T2 1=B1 2=B2 3=A1 4=B3 5=A2
6=A3; T3 1=A2 2=A1 3=A3 4=B1 5=B3 6=B2; T4 1=A1 2=A2 3=B3 4=B1 5=B2 6=A3.

## Takeaways / next

- Real excerpts in context made the pieces better at the piano, in every task, even though they
  did not change the large-scale plan (convergence above) and leaked some K. 545 figuration.
- Validation must check pitch spelling, not just parsing and bar sums: two misspelled files passed.
  Fixed (`malformed_pitch`).
- Next: automatic beaming (insert `L`/`J` by beat in a post-processing step rather than asking the
  generator); harder briefs closer to what the owner plays (Liszt, Rachmaninoff, Chopin études and
  ballades), which needs excerpts beyond the current corpus; more varied briefs to break the
  convergence; recheck the copy-check threshold on a fresh run.

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
