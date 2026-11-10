# **kern Encoding Reference (keyboard harmony)

> **Purpose:** Writing this compendium's chords, progressions, and piano textures as Humdrum
> `**kern` (replaces `theory/09`). Every ```` ```kern ```` block is a complete score that passes
> `experiments/generation/validate_notation.py` (music21 + Verovio).
>
> **Fields are separated by real TAB characters, never spaces.** A space inside a field means
> "chord": `4c 4e 4g`.

---

## 1. Primer

### File structure

A kern file is a grid. **Columns are spines** (one staff or annotation stream each), separated by
TABs. **Rows are time slices**: every row has exactly one field per active spine, and all fields on
a row start at the same moment.

```kern
**kern	**kern
*staff2	*staff1
*clefF4	*clefG2
*k[]	*k[]
*C:	*C:
*M4/4	*M4/4
=1	=1
2C	4e 4g 4cc
.	4f 4a 4cc
2G	2f 2g 2b
=2	=2
1C	1e 1g 1cc
==	==
*-	*-
```

| Line type | Starts with | Meaning |
| --- | --- | --- |
| Exclusive interpretation | `**` | Spine type, first line: `**kern`, `**harm`, `**dynam` |
| Tandem interpretation | `*` | Settings for one spine: clef, key, meter, staff. `*` alone = no change |
| Barline | `=` | `=1`, `=2` ... in every spine; `==` final barline |
| Data | anything else | Notes, chords, rests, or `.` (null: nothing new starts here) |
| Comment | `!!` / `!` | `!!` global comment (whole line); `!` local, one `!` per spine |
| Terminator | `*-` | Ends each spine; the last line of the file |

**Spine order: leftmost = lowest staff.** For piano: LH (bass staff) first, RH (treble) second.
Label them `*staff2` (LH) and `*staff1` (RH). Optional: `*part1` on both piano spines so they
share one instrument (brace). Annotation spines go to the **right of the kern spine they describe**
and carry the same `*staffN`.

### Tandem interpretations

| Token | Meaning |
| --- | --- |
| `*clefG2` / `*clefF4` | Treble / bass clef (`*clefC3` alto) |
| `*k[f#c#]` | Key signature: sharps in order F C G D A E B, flats `*k[b-e-a-]` in order B E A D G C F; `*k[]` none |
| `*C:` `*a:` `*A-:` `*f#:` | Key designation: uppercase = major, lowercase = minor, `-` = flat (`*A-:` not `*Ab:`) |
| `*M4/4` `*M3/4` `*M12/8` | Meter |
| `*MM96` | Tempo, quarter notes per minute |
| `*staff1` `*part1` | Staff / part assignment |

### Duration (recip): the number before the pitch

`1` whole, `2` half, `4` quarter, `8` eighth, `16` sixteenth, `32`. A dot adds half: `4.` dotted
quarter, `8.` dotted eighth, `2.` dotted half. **Tuplets** use the number that divides the whole
note: `12` = eighth-note triplet (three per quarter), `6` = quarter-note triplet (three per half),
`3` = half-note triplet, `24` = sixteenth triplet. Swing pair in 4/4: `6` + `12` = one beat.

### Pitch and octave

Letter case and repetition give the octave. Middle C = `c`.

| Octave | C2 | C3 | C4 (middle) | C5 | C6 |
| --- | --- | --- | --- | --- | --- |
| kern | `CC` | `C` | `c` | `cc` | `ccc` |

`B` = B3 (just below middle C), `b` = B4, `AAA` = A0 (lowest piano key). Octaves change at C:
`B`→`c` is a half step.

**Accidentals:** `#` sharp, `-` flat, `##` / `--` double, `n` explicit natural (display only).
**Pitch is absolute**: the key signature does not change what a token means. In `*k[b-e-a-]`, E-flat
is still `e-`; a bare `e` is E-natural (shown with a natural sign). **Write every accidental on
every note, every time.**

### Notes, chords, rests, ties, slurs

| Want | Write | Notes |
| --- | --- | --- |
| Note | `4c#` | duration, pitch, then signifiers |
| Chord | `4e 4g 4cc` | space-separated notes in one field; give each its duration |
| Rest | `4r` | whole-bar rest: `1r` (4/4), `2.r` (3/4) |
| Tie | `[2g` → `2g]` | `[` start, `_` middle, `]` end; in a chord, tie each note separately |
| Slur | `(8c` ... `8f)` | parsed by Verovio; music21 ignores slurs (no error) |
| Phrase | `{4g` ... `4e}` | same caveat |
| Grace note | `8qd` | on its **own row**, other spines `.`; never inside a chord field |
| Staccato / accent / tenuto | `4c'` `4c^` `4c~` | |
| Fermata | `1c;` | on one note of a chord is enough |

### Ornaments (style guide table → kern)

| Ornament | kern | Notes |
| --- | --- | --- |
| Trill, whole step | `T` (`4dT`) | choose by the real interval to the upper neighbor |
| Trill, half step | `t` (`4bt` in C) | Verovio prints the accidental implied by T/t |
| Mordent (main-lower-main) | `M` whole / `m` half | **parsers disagree**: music21 = lower mordent, Verovio draws an upper mordent |
| Upper mordent / Pralltriller | `W` whole / `w` half | music21 = upper (inverted) mordent, Verovio draws lower |
| Turn | `S` | inverted turn `$`; Verovio draws turns in red (flagged) |
| Appoggiatura | write it out as a real note | `P`/`p` exists but support is weak; prefer notated durations |

When the exact realization matters, write mordents and turns out as real short notes.

### Independent voices in one hand: spine split / merge

`*^` splits a spine into two (left subspine = upper voice, stems up; right = lower voice). `*v` on
**two adjacent** spines merges them. Manipulators sit on their own line with `*` in every other
spine. While split, every row has one more field.

### Dynamics: `**dynam`

Put a `**dynam` spine right of the RH spine, with `*staff1`. Tokens: `pp p mp mf f ff sfz fp`;
hairpins `<` (start cresc.) ... `[` (end), `>` (start dim.) ... `]` (end). Place each dynamic on a
row where the RH spine has a note (music21 drops dynamics on rows where the staff has `.`; it also
drops hairpins).

### Demo: split voices, triplets, slur, grace note, trill, fermata, dynamics

```kern
**kern	**kern	**dynam
*part1	*part1	*
*staff2	*staff1	*staff1
*clefF4	*clefG2	*
*k[f#]	*k[f#]	*
*G:	*G:	*
*M4/4	*M4/4	*
*MM96	*MM96	*
=1	=1	=1
2G	(4b	p
.	8cc	.
.	8dd	.
2C	4ee)	<
.	4dd	[
=2	=2	=2
*	*^	*
1D	4a	2d	mf
.	12b	.	.
.	12a	.	.
.	12g	.	.
.	4f#	2c	.
.	4a	.	.
*	*v	*v	*
=3	=3	=3
2GG	2g 2b	.
.	8qb	.
2D 2c	2aT	>
=4	=4	=4
1GG 1B	1g 1b 1dd;	]
==	==	==
*-	*-	*-
```

Note `4f#` in G major: the key signature does not supply the sharp.

### Mid-piece key and meter changes

Put the new tandems right after the barline, in **every** kern spine (use `*` in others):

```kern-fragment
=9	=9
*k[b-e-a-d-]	*k[b-e-a-d-]
*A-:	*A-:
*M3/4	*M3/4
```

### Swing and 12/8

For swing (blues, boogie, shuffle), **prefer 12/8**: each beat is `4.` and a long-short pair is
`4` + `8`. In 4/4 the equivalent is the triplet pair `6` + `12`. Straight `8` + `8` with a "swing"
text label is not machine-readable; avoid it.

```kern
**kern	**kern
*staff2	*staff1
*clefF4	*clefG2
*k[]	*k[]
*C:	*C:
*M12/8	*M12/8
=1	=1
4C	4.r
8E	.
4G	4g 4b- 4ee
8A	8r
4B-	4.r
8A	.
4G	4g 4b- 4ee
8E	8r
=2	=2
4F	4.r
8A	.
4c	4a 4cc 4ee-
8d	8r
4e-	4.r
8d	.
4c	4a 4cc 4ee-
8A	8r
=3	=3
2.C 2.G	2.e 2.b- 2.cc
==	==
*-	*-
```

---

## 2. Roman-numeral analysis: the `**harm` spine

Use one **`**harm` spine immediately right of the LH spine**, with `*staff2` and a key designation
(`*C:`). Verovio prints it as Roman numerals under the bass staff (`Ic` → I⁶₄, `-VII` → ♭VII, the
key as a `C:` prefix); music21 turns each token into a `RomanNumeral` in that key. Rules:

- **One harm token per chord change, on the same row as a LH note onset** (music21 attaches the
  label by row; a label on a row where the LH has `.` is silently dropped). Use `.` elsewhere.
- **Use only the `**harm` grammar below.** Figure digits are silently misread (`I64`, `V65`, `N6`
  become root-position `I`, `V`, `N`); other symbols (`bVII`, `vii°`, `Ger+6`, `It6`) make
  music21's whole parse fail.
- Change key with a key tandem in the harm spine (`*G:`) at the point of reinterpretation; free
  prose goes in `!!` global comments.

Alternatives load but carry no analysis: music21 ignores `**mxhm` (chord symbols) and turns
`**text` into lyrics; `!` comments are opaque strings.

**`**harm` grammar:** `[accidental] numeral [o|+] [7] [inversion] [/secondary]`

- Numeral case = quality: `I IV V` major, `ii iii vi` minor, `viio` diminished, `I+` augmented.
- Root accidental: `-` flat (`-VII`, `-III`, `-VI`), `#` sharp.
- Inversion letter: none = root, `b` = first (6), `c` = second (6/4), `d` = third (4/2).
  Cadential six-four = `Ic`; `V7b` = V6/5.
- Secondary: `V/V`, `V7/vi`, `viio7/V`.
- Special: `N` Neapolitan (`Nb` = N6), augmented sixths `Lt` Italian, `Fr` French, `Gn` German.
  With ♭6 in the bass write **`Ltb`, `Frc`, `Gnb`** (music21 reads these as It6, Fr4/3, Ger6/5;
  plain `Gn`/`Fr` put ♯4 / 2 in the bass).
- Minor keys (`*a:`): `i iio III iv V VI -VII viio`; `V` and `viio` include the raised leading
  tone, `-VII` is the natural subtonic, `VI` is diatonic.

### Chord vocabulary (C major; LH = bass, RH = a good close voicing)

| Chord | `**harm` | LH | RH | Notes |
| --- | --- | --- | --- | --- |
| I | `I` | `C` | `e g cc` | |
| ii | `ii` | `D` | `f a dd` | |
| iii | `iii` | `E` | `g b ee` | |
| IV | `IV` | `F` | `f a cc` | |
| V | `V` | `G` | `g b dd` | |
| vi | `vi` | `A` | `e a cc` | |
| vii° | `viio` | `B` | `d f b` | |
| V7 | `V7` | `GG` | `f g b` / `d f b` | B up to C; F down to E |
| Cadential I⁶₄ | `Ic` | `G` | `e g cc` | bass = 5; always goes to V(7) |
| V/V, V7/V | `V/V`, `V7/V` | `D` | `f# a dd` / `c f# a` | F# up to G |
| V7/ii | `V7/ii` | `A` | `c# e g` | |
| V/iii | `V/iii` | `B` | `d# f# b` | B D# F# |
| V7/IV | `V7/IV` | `C` | `e g b-` | V/IV alone = I |
| V7/vi | `V7/vi` | `E` | `e g# dd` | G# up to A; D down to C |
| iv (borrowed) | `iv` | `F` | `f a- cc` | A♭ down to G; no A♮ nearby (cross relation) |
| ♭VII | `-VII` | `BB-` | `d f b-` | B♭ D F |
| ♭III | `-III` | `E-` | `e- g b-` | E♭ G B♭ |
| Neapolitan ♭II⁶ | `Nb` | `F` | `f a- dd-` | D♭ F A♭, bass F (doubled); D♭ moves down |
| Augmented I⁺ | `I+` | `C` | `e g# cc` | C E G♯; G♯ up to A |
| Italian ⁺⁶ | `Ltb` | `A-` | `c f# cc` | A♭ C F♯ (C doubled) |
| French ⁺⁶ | `Frc` | `A-` | `c d f#` | A♭ C D F♯ |
| German ⁺⁶ | `Gnb` | `A-` | `e- f# cc` | A♭ C E♭ F♯, **F♯ not G♭**. Resolve to `Ic` (E♭ to E♮) to avoid parallel 5ths |

Augmented sixths: A♭ (bass) down to G, F♯ up to G, outward by half step. Don't put A♭ in the soprano.

---

## 3. Progression examples (C major, keyboard style)

LH = bass in root position (I⁶₄: 5 in the bass); RH = three upper voices. Checked for parallel
5ths/8ves, leading-tone and 7th resolution, and cross relations.

### 1. Authentic cadence: I–IV–I⁶₄–V7–I (soprano 8–8–8–7–8)

```kern
**kern	**harm	**kern
*part1	*	*part1
*staff2	*staff2	*staff1
*clefF4	*	*clefG2
*k[]	*	*k[]
*C:	*C:	*C:
*M4/4	*	*M4/4
=1	=1	=1
4C	I	4e 4g 4cc
4F	IV	4f 4a 4cc
4G	Ic	4e 4g 4cc
4GG	V7	4f 4g 4b
=2	=2	=2
1C	I	1e 1g 1cc
==	==	==
*-	*-	*-
```

V7 drops the bass an octave (G3 to G2), omits its 5th, and resolves B→C, F→E.

### 2. Deceptive cadence: I–IV–I⁶₄–V7–vi

```kern
**kern	**harm	**kern
*staff2	*staff2	*staff1
*clefF4	*	*clefG2
*k[]	*	*k[]
*C:	*C:	*C:
*M4/4	*	*M4/4
=1	=1	=1
4C	I	4e 4g 4cc
4F	IV	4f 4a 4cc
4G	Ic	4e 4g 4cc
4GG	V7	4d 4f 4b
=2	=2	=2
1AA	vi	1c 1e 1cc
==	==	==
*-	*-	*-
```

Complete V7 (RH D–F–B): as the bass rises G→A, the upper voices fall (no parallel 8ves). vi
doubles its third (C), the normal deceptive-cadence doubling.

### 3. Secondary dominant into deceptive cadence: I–IV–I⁶₄–V7/vi–vi (soprano 8–8–8–9–8)

```kern
**kern	**harm	**kern
*staff2	*staff2	*staff1
*clefF4	*	*clefG2
*k[]	*	*k[]
*C:	*C:	*C:
*M4/4	*	*M4/4
=1	=1	=1
4C	I	4e 4g 4cc
4F	IV	4f 4a 4cc
4G	Ic	4e 4g 4cc
4E	V7/vi	4e 4g# 4dd
=2	=2	=2
1AA	vi	1e 1a 1cc
==	==	==
*-	*-	*-
```

G→G♯ stays in one voice (no cross relation); G♯ rises to A, the 7th D falls to C, E is held.

### 4. Minor iv: I–iv–I⁶₄–V7–I

```kern
**kern	**harm	**kern
*staff2	*staff2	*staff1
*clefF4	*	*clefG2
*k[]	*	*k[]
*C:	*C:	*C:
*M4/4	*	*M4/4
=1	=1	=1
4C	I	4e 4g 4cc
4F	iv	4f 4a- 4cc
4G	Ic	4e 4g 4cc
4GG	V7	4f 4g 4b
=2	=2	=2
1C	I	1e 1g 1cc
==	==	==
*-	*-	*-
```

A♭ resolves down to G in the same voice; no A♮ appears in adjacent chords.

### 5. German augmented sixth: I–IV–I⁶₄–Ger⁺⁶–I⁶₄–V7–I

```kern
**kern	**harm	**kern
*staff2	*staff2	*staff1
*clefF4	*	*clefG2
*k[]	*	*k[]
*C:	*C:	*C:
*M4/4	*	*M4/4
=1	=1	=1
4C	I	4e 4g 4cc
4F	IV	4f 4a 4cc
4G	Ic	4e 4g 4cc
4A-	Gnb	4e- 4f# 4cc
=2	=2	=2
4G	Ic	4e 4g 4cc
4GG	V7	4f 4g 4b
2C	I	2e 2g 2cc
==	==	==
*-	*-	*-
```

The augmented sixth A♭3–F♯4 expands to G3–G4. E♭→E♮ and G→F♯→G each stay in one voice.

### 6. Pivot-chord modulation C → G (iii = vi)

```kern
**kern	**harm	**kern
*staff2	*staff2	*staff1
*clefF4	*	*clefG2
*k[]	*	*k[]
*C:	*C:	*C:
*M4/4	*	*M4/4
=1	=1	=1
4C	I	4g 4cc 4ee
4E	iii	4g 4b 4ee
4G	V	4g 4b 4dd
4C	I	4g 4cc 4ee
=2	=2	=2
4C	I	4g 4cc 4ee
!!pivot: E minor = iii in C = vi in G
*	*G:	*
4E	vi	4g 4b 4ee
2D	V7	2a 2cc 2ff#
=3	=3	=3
*k[f#]	*	*k[f#]
*G:	*	*G:
1GG	I	1g 1b 1gg
==	==	==
*-	*-	*-
```

Group 1 sets up C; group 2 reinterprets iii as vi of G. B sits below E in the iii chord, so
iii→D7 moves in contrary motion without parallel 5ths. `ff#` carries its sharp before the new key
signature.

### 7. Common-tone modulation C → A♭ (held C = 3rd of A♭)

```kern
**kern	**harm	**kern
*staff2	*staff2	*staff1
*clefF4	*	*clefG2
*k[]	*	*k[]
*C:	*C:	*C:
*M4/4	*	*M4/4
=1	=1	=1
4C	I	4e 4g 4cc
4F	IV	4f 4a 4cc
4G	Ic	4e 4g 4cc
4GG	V7	4f 4g 4b
=2	=2	=2
1C	I	1e 1g [1cc
!!common-tone modulation: C (1 in C) = 3 of A-flat; chromatic mediant
=3	=3	=3
*k[b-e-a-d-]	*	*k[b-e-a-d-]
*A-:	*A-:	*A-:
1AA-	I	1e- 1b- 1cc]
=4	=4	=4
2EE-	V7	2e- 2g 2dd-
2AA-	I	2e- 2a- 2cc
==	==	==
*-	*-	*-
```

The C is tied across the modulation while the harmony moves under it. The A♭ chord carries an
added 9th (B♭) for smoothness (`I` in harm; add-tones go in a comment). E→E♭ and G→B♭ are the only
moves. Then V7–I confirms A♭ (7th D♭ to C, leading tone G to A♭).

---

## 4. Key signatures

| Major / minor | Signature | Keys |
| --- | --- | --- |
| C / a | `*k[]` | `*C:` `*a:` |
| G / e | `*k[f#]` | `*G:` `*e:` |
| D / b | `*k[f#c#]` | `*D:` `*b:` |
| A / f♯ | `*k[f#c#g#]` | `*A:` `*f#:` |
| E / c♯ | `*k[f#c#g#d#]` | `*E:` `*c#:` |
| B / g♯ | `*k[f#c#g#d#a#]` | `*B:` `*g#:` |
| F♯ / d♯ | `*k[f#c#g#d#a#e#]` | `*F#:` `*d#:` |
| F / d | `*k[b-]` | `*F:` `*d:` |
| B♭ / g | `*k[b-e-]` | `*B-:` `*g:` |
| E♭ / c | `*k[b-e-a-]` | `*E-:` `*c:` |
| A♭ / f | `*k[b-e-a-d-]` | `*A-:` `*f:` |
| D♭ / b♭ | `*k[b-e-a-d-g-]` | `*D-:` `*b-:` |
| G♭ / e♭ | `*k[b-e-a-d-g-c-]` | `*G-:` `*e-:` |

---

## 5. Common mistakes (check before emitting)

1. **Field count ≠ spine count.** Every row, including `*` lines, barlines, and `*-`, has exactly
   one field per active spine. After `*^` there is one more; after `*v` one fewer.
2. **Spaces instead of TABs** between fields (or a TAB inside a chord). Between spines: TAB. Between
   chord notes: one space.
3. **Rows not time-aligned.** One row = one onset time. If a spine has no new note at that moment,
   its field is `.`. Each spine's durations must add up identically between barlines: an LH `2C`
   followed by RH `4e`, `4f` needs a second row `.<TAB>4f`.
4. **Accidentals left to the key signature.** `e` is always E♮. In E♭ major write `e-` every time;
   in G major write `f#` every time.
5. **Split/merge errors.** `*^` and `*v` are on their own line; `*v` must cover two adjacent
   subspines; every `*^` is merged before the end (or both subspines get `*-`).
6. **Missing `*-`** on the last line, or a missing `==` before it.
7. **Wrong octave or spine order.** `c` = middle C, `C` = C3, `GG` = G2. LH/bass spine first
   (left); annotation spines right of the kern spine they belong to.
8. **Bar durations wrong.** Each bar sums to the meter in every spine (`4.`+`8`+`2` = 4/4).
   Triplets come in complete groups (`12 12 12` = one quarter).
9. **`**harm` tokens outside the grammar.** `Ic`, `-VII`, `Gnb`, `Nb`, `V7/vi`; never `I64`,
   `bVII`, `Ger+6`, `N6`. One label per chord, on a row with an LH note.
10. **Grace notes in a chord field.** Give `8qd` its own row.
11. **Harmony slips:** parallel 5ths/8ves, unresolved leading tone or 7th, `G♭` for the German
    sixth's `F♯`, cross relations around borrowed or secondary chords.

### Output contract (paste into a system prompt)

```text
Output exactly one fenced code block tagged kern, containing a complete Humdrum **kern score
and nothing else inside the block. Fields are separated by single TAB characters; notes of a
chord are separated by single spaces. Skeleton (<TAB> = a real tab):

**kern<TAB>**harm<TAB>**kern<TAB>**dynam
*part1<TAB>*<TAB>*part1<TAB>*
*staff2<TAB>*staff2<TAB>*staff1<TAB>*staff1
*clefF4<TAB>*<TAB>*clefG2<TAB>*
*k[...]<TAB>*<TAB>*k[...]<TAB>*
*X:<TAB>*X:<TAB>*X:<TAB>*
*M4/4<TAB>*<TAB>*M4/4<TAB>*
*MM<bpm><TAB>*<TAB>*MM<bpm><TAB>*
=1<TAB>=1<TAB>=1<TAB>=1
<data rows: one row per onset time; '.' where a spine has no new event>
==<TAB>==<TAB>==<TAB>==
*-<TAB>*-<TAB>*-<TAB>*-

Rules: spine 1 = left hand (bass staff), spine 3 = right hand. Every row has 4 fields (more only
between *^ and *v). Pitches are absolute: write every sharp/flat on every note regardless of key
signature. Every bar sums to the meter in every kern spine. **harm tokens use the Humdrum
grammar (I, ii, V7, Ic, V7/vi, -VII, Nb, Ltb, Frc, Gnb, viio, I+) and sit on rows where the left
hand has a note. Omit the **harm or **dynam spine (and its column) if not needed.
```
