# Roadmap

This repo is general music-AI experiments, organised in tracks. Each track has its own goal and
stages, gated by milestones rather than dates; I stop to re-plan between stages rather than chase
every improvement.

## Tracks

| Track | Status | Where |
| ----- | ------ | ----- |
| [Generation](#generation) | Current focus, stage 1 | `experiments/generation/`, `experiments/NNN-gen-*` |
| [Optical music recognition](#optical-music-recognition) | Planned | |
| [Audio transcription](#audio-transcription) | Planned | |

The tracks share text formats (`**kern`, ABC), and later OMR and transcription can feed the
arranger by reading hymnals, lead sheets and recordings.

## Principles

- **Evaluation comes first.** Each track is measured the way its literature measures it (OMR-NED
  and CER for OMR, for example), and the evaluation is built before any training.
- **In generation, my judgment at the piano is the measure.** Automatic checks (validity, voice
  leading, playability, copying) catch errors; corpus statistics describe style. Neither is a
  target.
- **Every judged output is data.** Generations, ratings, notes, preferences and corrections go into
  [`feedback/`](feedback/README.md) in a machine-readable form.
- **Public by default**, except copyrighted material: pop songs, modern arrangers' scores and
  paper PDFs stay local (`data/`, `notes/`, `research/` are gitignored).

## Generation

Generate **musically advanced piano arrangements of songs I know** (hymns, Christmas music, pop),
at a chosen difficulty and style, that I'd want to practise and perform: the tune clearly
recognisable, the texture idiomatic and advanced, the engraving clean.

A second goal is **music for ballet classes**: each exercise calls for a specific style with
specific phrasing rules (marches, waltzes, polkas, triple adage, rags, ...), written fresh or
adapted from pop songs to fit the phrasing.

The long-term aim is a model I train and run locally (an open-weight LLM fine-tuned on my
feedback). Until then, prompting hosted models is the quick way to map what's possible, build the
evaluation tools, and learn what good output looks like.

### Stages

0. **Feedback dataset** (done): `feedback/` tables, `music_ai.feedback`, experiments 001–002
   imported.
1. **Christmas hymn arrangements.** Tunes: *O Come, All Ye Faithful*, *Hark! The Herald Angels
   Sing*, *Joy to the World*, *Silent Night*, *The First Noel* (public domain).
   _Done when:_ there's an arrangement I'd play this December.
   - Round 1 (003, done): beaming, melody-fidelity check, hymn sources, one-pass generation. All
     valid, none playable as is; the arranging guide prescribed a single plan that every piece
     followed.
   - Round 2, in order:
     1. **Study real arrangements.** Line each original up against its arrangement (my
        three; Liszt's Ständchen, Erlkönig, Die Forelle, Liebestraum No. 3) and describe
        the changes: melody notes kept, swapped or ornamented, rhythm stretched or compressed,
        which hand has the tune, where harmony and melody change together. Write per-piece
        technique notes with bar references, reviewed by me (notes on my own
        arrangements stay local).
     2. **Planning pass.** Before writing notes, the generator writes a plan: style and reference
        excerpts, the story of each verse from its words, a harmonic plan citing the theory docs
        (including how long each modulation takes), texture per section, a short countermelody
        motif. I review every plan (for as long as that's worth it); plan reviews go into
        `feedback/` too.
     3. **Left-hand checks.** Automatic checks for my mechanical rules (low sevenths,
        close intervals in the bass, chains of large leaps, one pattern for a whole verse), fixed
        by the generator before judging.
     4. **Judging with comments on specific notes, chords or bars**, tied back to the kern.
     5. **004:** the five hymns again with all of the above, aiming at difficulty 4.
2. **Difficulty ladder.** Define difficulty with measurable proxies (density, span, hand
   independence, range, inner voices), calibrated on pieces I rate easy or hard; aim at "advanced"
   on purpose. The Liszt corpus gives advanced examples to calibrate against.
3. **Better generation process.** Validator and renderer in the loop with revision; further
   separate passes (harmony sketch, texture, engraving) beyond the planning pass; a fixed
   benchmark of briefs rerun as models change; compare models.
4. **Pop arrangements and ballet styles.** Pop needs a melody input (typed, MIDI, or transcribed)
   and stays local-only. Ballet styles follow my rules per exercise.
5. **Training.** Fine-tune an open-weight model (supervised on good examples, then preference
   learning on feedback). Its own outputs have to be judged too: preference training works best on
   the trained model's own samples. Hosted-model outputs come with terms that restrict training on
   them, so this may start from fresh data.

### Done so far

- 001: ABC vs `**kern` pilot. Both valid; output correct but textbook-bland.
- 002: real-composer excerpts in context. Rated clearly better blind (musicality 4.9 vs 3.9 of 5);
  found the misspelled-pitch and missing-beam notation problems.
- Stage 1 tooling: automatic beaming, pitch-spelling check, melody-fidelity check, five
  public-domain hymn sources with every verse's words (`**text` spines).
- 003: ten hymn arrangements, all valid, tune kept literally on top. None playable as is (best:
  Silent Night H4-2, "with fixes"); difficulty 2–3, below the brief. All ten converged on one plan
  (pedal intro, V-of-new-key modulation, ♭VI deceptive cadence, iv–I tag, eighth-note broken-chord
  left hand) that the arranging guide had prescribed. My detailed notes are kept
  locally; the scores are in `feedback/`.
- After 003: the arranging guide was rewritten as an index into the theory docs plus my
  rules from 003, with no prescribed form.
- Reference corpus (local, `data/`): my three arrangements; four originals paired with
  Liszt's piano versions (Ständchen, Erlkönig, Die Forelle, Liebestraum No. 3 / "O lieb"); and
  "Widmung", "Ave Maria", Consolations 1 and 4, Bénédiction. Converted from MusicXML by
  `scripts/musicxml_to_kern.py`, kept only if every note matches the source.

## Optical music recognition

Read photos and scans of printed sheet music (any instrumentation) into symbolic notation. The
approach and evaluation are in the [README](README.md#optical-music-recognition). Each stage is
trained and evaluated before the next:

0. **Evaluation harness**: OMR-NED and CER on a fixed test set, and an Audiveris baseline.
1. **Camera-PrIMuS**: monophonic single-staff incipits with simulated camera distortion; a
   laptop-trainable baseline.
2. **GrandStaff**: polyphonic two-staff piano scores.
3. **Rendered OpenScore Lieder**: voice and piano with lyrics, rendered synthetically at scale.
4. **Real-world photos**: fine-tune and evaluate on photographed and scanned scores of all kinds,
   compared against Audiveris.

Open questions to settle by experiment: frozen encoder plus trained decoder vs fine-tuning a
vision-language model vs training from scratch, and ABC vs `**kern` as the output format.

## Audio transcription

Turn audio recordings into notation. Not yet scoped.
