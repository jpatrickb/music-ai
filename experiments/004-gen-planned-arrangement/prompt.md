# 004 pilot prompt

Each sample is one fresh Claude Code agent (subagent) given the prompt below, with `{OUT}` filled
in. Two samples (P1-1, P1-2) from the same approved plan.

## Prompt

```text
You are writing a solo-piano arrangement of the hymn "Silent Night" in Humdrum **kern, from an
approved plan. Repo root: /Users/josephbeal/Documents/personal/music-ai (paths below are relative
to it). Read AGENTS.md first: never commit; don't run Verovio directly.

Read these files before writing:
- experiments/generation/arranging/examples/plan-silent-night.md: THE PLAN, approved by me.
  Follow it: form, keys, tune placement per verse, textures, harmony departures, modulations,
  motif. Where it's approximate (bar counts), use judgement.
- experiments/generation/arranging/02-planning.md and 01-hymn-arrangement.md: the guides, including
  my rules (marked "mine") for left-hand spacing, leaps, doubling, 6/4 chords,
  modulation craft, and tune and accompaniment on the same key.
- The reference notes the plan cites, in experiments/generation/arranging/references/:
  liszt-liebestraum-3.md, liszt-standchen.md, liszt-widmung.md, liszt-un-sospiro.md. Then look at
  the cited bars in the Liszt kern files themselves (data/liszt/kern/liszt-liebestraum-3-s541.krn,
  liszt-standchen-s560-7.krn, liszt-widmung-s566.krn, liszt-un-sospiro-s144-3.krn) to see the
  textures concretely. They're models of texture and craft; don't quote them.
- experiments/generation/theory/02, 03, 06 and 07 (cadences, secondary dominants, common-tone
  modulation, augmented sixths): the harmony and modulations in the plan cite these.
- experiments/generation/encoding/kern-reference.md: how to write the kern.
- experiments/generation/sources/hymns/stille-nacht.krn: the hymn (B♭ major, 6/8; soprano = the
  tune; **text spines hold all four verses' words).

Requirements:
- Two staves: one **kern spine for the left hand (*staff2, *clefF4) and one for the right hand
  (*staff1, *clefG2), each split (*^ / *v) into voices where needed. Every bar must add up in every
  spine. Number the bars. Title record: !!!OTL: Silent Night (piano arrangement).
- Include a tempo (*MM), and dynamics in a **dynam spine. Pedal marks (*ped / *Xped) are welcome.
  Don't write beam markers (L, J); beams are added automatically.
- Mark the stems so the hand is clear where the tune passes between the hands: `/` (stem up) for
  right-hand notes and `\` (stem down) for left-hand notes in the passages where hands cross or
  share the tune (the convention in Un sospiro's footnote).
- No block chord wider than a ninth in one hand; wider spans as broken chords or rolled (`` ` ``
  after a chord isn't needed, just keep each hand within a ninth).
- You may check your file with:
    uv run python experiments/generation/validate_notation.py {OUT}
  and fix any errors it reports. Don't run any other code.
- Write the finished score with the Write tool to exactly: {OUT}
- When done, reply with a short description: sections with bar numbers, keys, where the tune is,
  textures, and anywhere you departed from the plan and why.
```
