# LLM Music Generation

In-context reference material for having LLMs compose and arrange piano/keyboard music as text.
Models write **ABC** or **`**kern`**. Never have them write MusicXML or MIDI directly: those are
conversion targets, produced from validated ABC/kern with `music21`.

## Layout

| Path                     | Contents                                                                 |
| ------------------------ | ------------------------------------------------------------------------ |
| [`theory/`](theory/)     | Tonal harmony compendium, 01–08. Notation-neutral: prose + Roman numerals |
| [`styles/`](styles/)     | Piano style guides, 01–06 (Baroque → Latin/folk). Notation-neutral       |
| [`encoding/`](encoding/) | One reference per output format, all examples parser-validated           |
| [`arranging/`](arranging/) | Arranging and planning guides, an example plan, and per-piece notes on Liszt's song transcriptions (`references/`) |
| [`sources/hymns/`](sources/hymns/) | Public-domain hymnal settings in kern (written by `scripts/fetch_hymns.py`), the tunes for 003–004 |
| `validate_notation.py` | Parses ABC/kern with music21 and Verovio; checks bar durations, alignment and pitch spelling |
| `harmony_check.py`     | Voice-leading checks: parallels, leading-tone and seventh resolution, spacing |
| `playability_check.py` | Hand span, leap size, hand crossing, chromatic clashes, and copying from in-context excerpts |
| [`tests/`](tests/)     | Tests for the three checkers (run by `uv run pytest`) |

- [`encoding/abc-reference.md`](encoding/abc-reference.md): ABC primer, chord vocabulary,
  progressions, common mistakes, output contract
- [`encoding/kern-reference.md`](encoding/kern-reference.md): the same content in Humdrum `**kern`

The two encoding references cover the same musical content, so ABC vs `**kern` can be run as a
controlled comparison: same theory/style context, same task, only the encoding reference swapped.

## Building a prompt

1. **System prompt:** the chosen encoding reference (in full; its "output contract" section
   defines the exact skeleton to emit), plus the theory and/or style files relevant to the task.
   Don't include both encoding references: mixing formats invites hybrid output.
2. **User prompt:** the task, e.g. "16-bar piece in A♭ major, Romantic style, modulating to C via
   common-tone modulation, ending with a German augmented sixth cadence".

## Validating and listening

```sh
# parse with music21 + Verovio, check every bar's duration against the meter
uv run experiments/generation/validate_notation.py outputs/gen/piece.abc
# also render page 1 to SVG
uv run experiments/generation/validate_notation.py outputs/gen/piece.krn --svg outputs/gen/renders
# convert to MIDI / MusicXML for playback or notation software
uv run python -c "import music21,sys; s=music21.converter.parse(sys.argv[1]); s.write('midi', fp=sys.argv[1]+'.mid'); s.write('musicxml', fp=sys.argv[1]+'.musicxml')" outputs/gen/piece.abc
```

The validator also accepts Markdown and checks every ` ```abc ` / ` ```kern ` block, which is how
the encoding references are kept correct. Run it after editing them. It checks syntax and rhythm,
not harmony: parallel fifths and wrong chord spellings still need a music-theory check.

Commands run from the repo root. The checkers' tests run with the rest: `uv run pytest`.
