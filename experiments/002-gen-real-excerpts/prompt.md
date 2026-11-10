# 002 prompt and tasks

Each sample is one fresh Claude Code teammate agent given the prompt below, with `{TASK}`,
`{CONTEXT}`, `{EXCERPTS}` and `{OUT}` filled in. Arm A and arm B prompts are identical except for
the excerpt paragraph, which arm A omits.

## Prompt template

```text
You are composing a short original piano piece and writing it in Humdrum **kern.

Read these files, and only these files, before writing (paths are relative to the repo root):
{CONTEXT}
{EXCERPTS}
Task:
{TASK}

Requirements:
- Two staves for piano: one **kern spine for the left hand (*staff2, *clefF4) and one or more
  for the right hand (*staff1, *clefG2), following the kern reference. Spine splits (*^ / *v)
  are allowed for independent voices within a hand.
- Every bar must add up to the time signature in every spine. Include bar numbers.
- A **harm Roman-numeral spine is optional.
- Write it so a good amateur pianist could sight-read it: no stretches beyond a ninth in one
  hand.
- Do not run any code or shell commands, and do not read any other files. Work it out on your
  own, then write the finished score with the Write tool to exactly this path: {OUT}
- When done, reply with one short paragraph describing the piece (form, keys, main idea).
```

Arm B's excerpt paragraph (`{EXCERPTS}`):

```text
Also read these excerpts of real music in the target style, in **kern. They show how the
composer handles texture, bass lines, inversions, non-chord tones and phrasing. Learn from
them, but write your own music: do not copy their melodies, bass lines or progressions.
{EXCERPT_FILES}
```

## Tasks

| ID  | Brief (`{TASK}`)                                                                                                                                                                                                                                                                                                                           | Context (`{CONTEXT}`, both arms; plus `experiments/generation/encoding/kern-reference.md`) | Excerpts (arm B), from `data/excerpts/002/` (cut by `scripts/cut_kern_excerpt.py`)                         |
| --- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------ | ---------------------------------------------------------------------------------------------------------- |
| T1  | A Romantic piano prelude in G minor in the style of Chopin's Preludes Op. 28, 16–24 bars, any meter. One main idea and one consistent accompaniment texture throughout, a singing melody over the left hand, expressive chromatic harmony, and a clear final authentic cadence in G minor.                                                 | theory/01, theory/03, theory/04, styles/01                                                 | `chopin-prelude-op28-4.krn` (Op. 28/4, bars 1–12), `chopin-prelude-op28-15.krn` (Op. 28/15, bars 1–8)      |
| T2  | The exposition of a Classical piano sonata first movement in D major in the style of Mozart, 28–40 bars, 4/4. First theme in D major, a transition that modulates, a second theme in A major, and a closing section ending with a perfect authentic cadence in A major. Use typical Classical accompaniment figures (e.g. Alberti bass).   | theory/01, theory/02, theory/03, theory/05, styles/01                                      | `mozart-k545-i.krn` (K. 545/i, bars 1–13), `mozart-k332-i.krn` (K. 332/i, bars 1–12)                       |
| T3  | A two-part invention in E minor in the style of J. S. Bach, 14–20 bars, 4/4. Two independent contrapuntal voices (one per hand), built on a short subject stated in one voice and imitated in the other, with sequences and a cadence in a related key (e.g. G major or B minor) before returning to end in E minor.                       | theory/01, styles/01                                                                       | `bach-invention-1.krn` (Invention 1, bars 1–7), `bach-invention-8.krn` (Invention 8, bars 1–12)            |
| T4  | A classic piano rag in F major in the style of Scott Joplin, 2/4: a 4-bar introduction, a 16-bar A strain and a 16-bar B strain (36 bars; write out any repeats). Left hand in the oom-pah pattern (bass note or octave on the beat, chord on the off-beat), right hand syncopated, with chromatic passing tones and a secondary dominant. | theory/01, theory/03, styles/03                                                            | `joplin-maple-leaf.krn` (Maple Leaf Rag, bars 1–16), `joplin-entertainer.krn` (The Entertainer, bars 5–20) |

Keys were chosen to differ from the excerpts' keys, so close copying is easier to spot. Output
paths: `experiments/002-gen-real-excerpts/samples/{A,B}/T{n}-{k}.krn`, k = 1–3.
