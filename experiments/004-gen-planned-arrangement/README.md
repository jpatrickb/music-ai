# 004 (pilot): an arrangement written from an approved plan

## Question / hypothesis

Round 2 of roadmap stage 1. Does writing from a plan I approved first, with real
arrangements as references (Liszt's song transcriptions and Un sospiro, studied in
`experiments/generation/arranging/references/`), fix what 003 lacked: style, a story, purposeful
harmony, varied texture, modulation craft, and difficulty? This is a pilot on one hymn, before the
left-hand checks and the comment-on-the-score judging page (round-2 steps 3–4) are built.

## Setup

- **Plan:** `experiments/generation/arranging/examples/plan-silent-night.md`, written to the format
  in `02-planning.md` and approved by me unchanged.
- **Prompt:** [`prompt.md`](prompt.md). The context is the plan, the guides, the cited Liszt notes and
  their kern, theory 02/03/06/07, the kern reference and the hymn source.
- **Generator:** two independent Claude Code agents (`claude-opus-5-5`), same prompt, run
  2026-11-11. Unlike 003, they could run the notation validator (and nothing else). P1-1 also ran
  one Python edit, against the prompt. It reported this itself and made all later changes with
  the editing tool.
- **Samples:** `samples/P1-1.krn`, `samples/P1-2.krn`. P1-2 is rendered as a PDF and MP3 in [`renders/`](renders/) by
  `scripts/render_scores.py`.

## Results

### Automatic checks

| Piece | Bars | Valid | Tune placement (phrase map) | Playability flags |
| ----- | ---: | ----- | --------------------------- | ----------------- |
| P1-1  | 67 | yes | all 24 phrase statements at 100%, placed as the plan says: verse 1 middle at pitch (5–16), verse 2 tenor an octave down (17–30), verse 3 in G♭ on top (36–47), verse 4 on top (50–59), coda (62–63) | wide RH spans in verse 4, mostly the crossing LH counted as RH by staff |
| P1-2  | 67 | yes | (not yet mapped) | 13 high, same passage |

Both followed the plan and made the same two departures:
- **The cadenza ends on an F7 chord, not a pickup:** Silent Night has no pickup, which was a mistake
  in the plan.
- **Verse 3 sits a sixth above the voice,** to leave room for the arpeggio below.

### My judging

Pending. A private listening and rating page was built with the same format as 003. I have
comments to write up.

## Takeaways / next

To be written after judging.
