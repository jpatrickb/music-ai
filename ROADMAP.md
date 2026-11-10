# Roadmap

## Goal

Generate **musically advanced piano arrangements of songs I know** (hymns, Christmas music, pop),
at a chosen difficulty and style, that I'd want to practise and perform: the tune clearly
recognisable, the texture idiomatic and advanced, the engraving clean.

A second goal is **music for ballet classes**: each exercise calls for a specific style with
specific phrasing rules (marches, waltzes, polkas, triple adage, rags, ...), written fresh or
adapted from pop songs to fit the phrasing.

The long-term aim is a model I train and run locally (an open-weight LLM fine-tuned on my
feedback). Until then, prompting hosted models is the quick way to map what's possible, build the
evaluation tools, and learn what good output looks like.

## Tracks

- **Generation** (main focus): `experiments/generation/` and `experiments/NNN-gen-*`.
- **OMR** (parallel track): score image to symbolic notation, following the plan in the
  [README](README.md#omr-track). Later it can feed the arranger by reading hymnals and lead sheets.

## Principles

- **The owner's judgment at the piano is the measure.** Automatic checks (validity, voice leading,
  playability, copying) catch errors; corpus statistics describe style. Neither is a target.
- **Every judged output is data.** Generations, ratings, notes, preferences and corrections go into
  [`feedback/`](feedback/README.md) in a machine-readable form.
- **Public by default**, except copyrighted material: pop songs, modern arrangers' scores and
  paper PDFs stay local (`data/`, `notes/`, `research/` are gitignored).
- Set goals per stage and stop to re-plan between stages, rather than chasing every improvement.

## Generation stages

Gated by milestones, not dates.

0. **Feedback dataset** (done): `feedback/` tables, `omr_lab.feedback`, experiments 001–002
   imported.
1. **Christmas hymn arrangements.** Tunes: *O Come, All Ye Faithful*, *Hark! The Herald Angels
   Sing*, *Joy to the World*, *Silent Night*, *The First Noel* (public domain). Build: a
   melody-and-harmony input format, automatic beaming, a melody-fidelity check, an arrangement
   brief (introduction, verse, varied verse, optional key change, ending). Blind-judge as in 002.
   _Done when:_ there's an arrangement I'd play this December.
2. **Difficulty ladder.** Define difficulty with measurable proxies (density, span, hand
   independence, range, inner voices), calibrated on pieces I rate easy or hard; aim at "advanced"
   on purpose. Needs advanced public-domain piano examples (Liszt, Rachmaninoff, Chopin, Grieg),
   so a corpus-sourcing step.
3. **Better generation process.** Validator and renderer in the loop with revision; separate
   passes (form plan, harmony sketch, texture, engraving); a fixed benchmark of briefs rerun as
   models change; compare models.
4. **Pop arrangements and ballet styles.** Pop needs a melody input (typed, MIDI, or transcribed)
   and stays local-only. Ballet styles follow the owner's rules per exercise.
5. **Training.** Fine-tune an open-weight model (supervised on good examples, then preference
   learning on feedback). Its own outputs have to be judged too: preference training works best on
   the trained model's own samples. Hosted-model outputs come with terms that restrict training on
   them, so this may start from fresh data.

## Done so far

- 001: ABC vs `**kern` pilot. Both valid; output correct but textbook-bland.
- 002: real-composer excerpts in context. Rated clearly better blind (musicality 4.9 vs 3.9 of 5);
  found the misspelled-pitch and missing-beam notation problems.
