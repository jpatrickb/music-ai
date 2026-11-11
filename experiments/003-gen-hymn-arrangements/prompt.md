# 003 prompt and tasks

Each sample is one fresh Claude Code teammate agent given the prompt below, with `{TITLE}`,
`{SOURCE}`, `{KEY}` and `{OUT}` filled in. All samples get the same prompt otherwise (one
condition, no arms).

## Prompt template

```text
You are arranging a hymn for solo piano and writing the arrangement in Humdrum **kern.

Read these files, and only these files, before writing (paths are relative to the repo root
/Users/josephbeal/Documents/personal/music-ai):
- experiments/generation/encoding/kern-reference.md
- experiments/generation/arranging/01-hymn-arrangement.md
- experiments/generation/theory/01-voice-leading-fundamentals.md
- experiments/generation/theory/02-cadences-and-substitutions.md
- experiments/generation/theory/03-secondary-dominants.md
- experiments/generation/theory/04-borrowed-chords-modal-mixture.md
- experiments/generation/theory/05-pivot-chord-modulation.md
- experiments/generation/styles/01-baroque-classical-romantic.md
- {SOURCE} (the hymn to arrange: the four-part hymnal setting, soprano = the tune)

Also read these excerpts of Romantic piano music in **kern. They are models of piano texture
only (a singing melody over a rich, flowing accompaniment, wide left-hand spacing, inner voices);
don't quote them.
- data/excerpts/003/chopin-prelude-op28-17.krn (Chopin, Prelude Op. 28 No. 17, bars 1–12)
- data/excerpts/003/chopin-prelude-op28-13.krn (Chopin, Prelude Op. 28 No. 13, bars 1–12)

Task:
An advanced solo-piano arrangement of "{TITLE}" from the hymnal setting above. About 2–3 minutes
at your chosen tempo: an introduction, at least two complete statements of the tune with the
second clearly varied in texture and harmony, an optional key change before the last statement,
and an ending. Keep the tune's notes and rhythm recognisable and mostly on top. Start in the
hymnal's key ({KEY}). Write for an advanced amateur pianist who will practise it: noticeably more
demanding and richer than the hymnal setting, with flowing accompaniment and a full texture at
the climax, but idiomatic and comfortable under the hands.

Requirements:
- Two staves for piano: one **kern spine for the left hand (*staff2, *clefF4) and one or more
  for the right hand (*staff1, *clefG2), following the kern reference. Spine splits (*^ / *v)
  are allowed for independent voices within a hand.
- Every bar must add up to the time signature in every spine. Include bar numbers.
- Put the title in a reference record: !!!OTL: {TITLE} (piano arrangement)
- A tempo (*MM), dynamics (a **dynam spine) and pedal marks (*ped / *Xped) are welcome.
- No block chord wider than a ninth in one hand; wider intervals only as broken chords.
- Don't write beam markers (L, J); beams are added automatically.
- Do not run any code or shell commands, and do not read any other files. Work it out on your
  own, then write the finished score with the Write tool to exactly this path: {OUT}
- When done, reply with one short paragraph describing the arrangement (sections with bar
  numbers, keys, textures).
```

## Tasks

| ID  | Hymn (`{TITLE}`)               | Tune             | Source (`{SOURCE}`, `experiments/generation/sources/hymns/`) | Key (`{KEY}`) | Hymnal meter |
| --- | ------------------------------ | ---------------- | ------------------------------------------------------------ | ------------- | ------------ |
| H1  | O Come, All Ye Faithful        | ADESTE FIDELES   | `adeste-fideles.krn`                                         | G major       | 4/4          |
| H2  | Hark! The Herald Angels Sing   | MENDELSSOHN      | `mendelssohn.krn`                                            | F major       | 4/4          |
| H3  | Joy to the World               | ANTIOCH          | `antioch.krn`                                                | D major       | 2/4          |
| H4  | Silent Night                   | STILLE NACHT     | `stille-nacht.krn`                                           | B♭ major      | 6/8          |
| H5  | The First Noel                 | THE FIRST NOWELL | `the-first-nowell.krn`                                       | D major       | 3/4          |

Sources: Open Hymnal Project (public domain), converted by `scripts/fetch_hymns.py`. Excerpts:
`data/excerpts/003/`, cut by `scripts/cut_kern_excerpt.py` from the pinned Chopin preludes
collection (Op. 28 No. 17 bars 1–12, No. 13 bars 1–12). Output paths:
`experiments/003-gen-hymn-arrangements/samples/H{n}-{k}.krn`, k = 1–2.
