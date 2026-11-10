# ABC Notation Reference (Piano, Keyboard Style)

> **Purpose:** How to write piano music for this compendium in ABC, and how every chord type from
> `theory/01–08` looks in ABC. **Toolchain:** output is parsed by music21 and rendered by Verovio.
> Some legal ABC is mishandled by them; this doc teaches only the subset they read correctly.
> Rules marked **(toolchain)** are stricter than the ABC 2.1 standard on purpose. (Verovio's own ABC
> import is single-voice and ignores key changes, so grand-staff renders go through music21.)

---

## 1. Primer

### Header

| Field | Meaning                  | Example                    |
| ----- | ------------------------ | -------------------------- |
| `X:`  | Tune number, first line  | `X:1`                      |
| `T:`  | Title                    | `T:Nocturne in Ab`         |
| `M:`  | Meter                    | `M:4/4`, `M:3/4`, `M:12/8` |
| `L:`  | Unit note length         | `L:1/8` (a bare note = ♪)  |
| `Q:`  | Tempo                    | `Q:1/4=72`                 |
| `V:`  | Voice declaration        | `V:2 clef=bass name="LH"`  |
| `K:`  | Key, **last header line** | `K:Ab`, `K:F#m`, `K:D dor` |

### Pitch and octave

`C D E F G A B` = C4–B4 (C4 is middle C). `c d e f g a b` = C5–B5. Each `'` raises an octave, each
`,` lowers one: `c'` = C6, `C,` = C3, `C,,` = C2. So the bass-clef staff (G2–A3) is `G,, A,, B,, C,
D, E, F, G, A,`; the treble staff (E4–F5) is `E F G A B c d e f`.

### Durations (multiples of `L`)

With `L:1/8`: `c` = ♪, `c2` = ♩, `c3` = dotted ♩, `c4` = half, `c8` = whole, `c/2` (or `c/`) = 16th.
With `L:1/4`: `c` = ♩, `c2` = half, `c4` = whole, `c/` = ♪. Rests: `z` with the same suffixes (`z2`).
A chord takes its length after the bracket: `[CEG]4`. Every note inside a chord sounds for that
length; never put different lengths inside one chord.

- **Broken rhythm:** `c>d` = dotted first + short second (`c3/2 d/2`); `c<d` = the reverse.
- **Tuplets:** `(3cde` = three notes in the time of two. `(3` counts the next three notes.
- **Ties:** `c2-c2` (same pitch both sides). Chords: `[CEG]2-[CEG]2`.
- **Slurs:** `(cdef)`.
- **Grace note:** `{a}g` (acciaccatura `{/a}g`). Zero duration; does not count in the bar.
- **Bars:** `|`, double `||`, final `|]`, repeats `|: ... :|`, endings `|1 ... :|2 ... |]`.

### Accidentals (read this twice)

`^` sharp, `_` flat, `=` natural, `^^`/`__` double. `K:` supplies the default: in `K:Ab`, a bare `E`
is E♭ and `=E` is E♮.

**(toolchain)** In standard ABC an accidental lasts to the end of the bar. **music21 does not do
this**: it reads `^F G F` as F♯ G F♮ and `^F2-F2` as F♯ tied to F♮. So:

1. Write the accidental on **every** altered note, every time, even repeated in the same bar and on
   both sides of a tie: `^F G ^F`, `^F2-^F2`.
2. When a letter returns to its key-signature pitch later in the same bar, mark it explicitly:
   `^c2 =c2` (C♯ then C♮ in C major); in `K:Ab`, `=E E` is ambiguous, so write `=E _E`.

Both rules are legal standard ABC, so every reader agrees on the pitches.

### Chord symbols and analysis

`"G7"[FGB]`: a plain quoted string before a note is a **chord symbol** and must be a real one (`C`,
`Am`, `G7`, `C/G`, `Bdim`, `C+`, `Abadd9`, `F#7`). music21 silently drops anything else, so Roman
numerals go in an **annotation** with a placement prefix: `"_V7/vi"` (below the staff) or `"^text"`
(above). Convention here: chord symbols above the right hand, Roman numerals below the left hand.
Free-text comments are `%` lines.

### Grand staff (two voices)

Declare both voices in the header, then write **all** of voice 1 (any number of lines) after a line
containing only `V:1`, then **all** of voice 2 after a line `V:2`. **(toolchain)** Never use inline
`[V:1]` and never switch back to a voice you already left; music21 splits or merges the parts.
Both voices must contain the same number of bars with the same total duration per bar. A `% bar 5`
comment at the start of each line helps alignment.

### Key and meter changes mid-piece

**(toolchain)** music21 ignores inline fields (`[K:Ab]`, `[M:3/4]`) and parses them as junk. Write
every change as a **pair of lines, `M:` then `K:`**, at a barline, **in every voice**, restating
whichever one did not change. music21 applies a lone `M:` or `K:` line to the notes but does not
record the new signature in the score.

```abc-fragment
V:1
[CEG]4 |
M:3/4
K:C
[DFA]3 | [CEG]3 |]
```

(Key changes are validated in examples 6 and 7 below. This meter-change fragment is not validated
because the validator's per-bar check mislabels the first bar after a meter change.)

### Decorations and dynamics

Place decorations before the note (after any chord symbol): `"G7"!trill!f4`. Always use the long
`!name!` form. **(toolchain)** The single-letter shortcuts (`T`, `H`, `M`, `P`, `~`, `L`, `S`, `O`,
`u`, `v`) can make music21 drop notes. music21 ignores decorations; Verovio draws them.

| Ornament (styles/01)        | ABC              | Other marks     | ABC                   |
| --------------------------- | ---------------- | --------------- | --------------------- |
| Trill                       | `!trill!`        | Fermata         | `!fermata!`           |
| Lower mordent               | `!mordent!`      | Accent          | `!>!`                 |
| Upper mordent/Pralltriller  | `!uppermordent!` | Staccato        | `.c`                  |
| Turn                        | `!turn!`         | Dynamics        | `!pp! !p! !mf! !f! !ff! !sfz!` |
| Appoggiatura (long, on beat) | write it out as a real note  | Cresc./dim. | `"^cresc."`, `"^dim."` |

Hairpins (`!crescendo(!`/`!<(!`) are not drawn by Verovio 6.4; write `"^cresc."` instead. Baroque
appoggiaturas take real time, so write them as notated notes, not as `{grace}` notes.

### Swing and 12/8

Per `styles/03`, prefer **12/8** for swing and boogie: each beat is three ♪, so long-short swing is
`c2 d` (♩♪). Alternatively write straight eighths in 4/4 with `"^Swing"` above bar 1. Do not use `>`
for swing; `c>d` is a hard dotted rhythm (3:1), not triplet swing (2:1).

### Primer demo

```abc
X:1
T:Primer demo
M:4/4
L:1/8
Q:1/4=88
K:G
V:1 clef=treble name="RH"
V:2 clef=bass name="LH"
V:1
% bars 1-4: slur, grace, trill, triplet, broken rhythm, explicit accidentals, endings
|: "G"!p!(B2 d2) {a}g3 a | "D7"!trill!f4 (3efg a2 | "Em"!f!g>f e>d "A7"^c2 "D7"=c2 |1 "G"B6 z2 :|2 "G"!fermata!B8 |]
V:2
|: G,,2 [D,G,]2 G,,2 [D,G,]2 | D,2 [A,C]2 D,2 [A,C]2 | E,2 [G,B,]2 A,,2 D,2 |1 G,,4- G,,2 z2 :|2 [G,,D,]8 |]
```

### Swing demo (12/8 boogie)

```abc
X:1
T:Boogie in 12/8
M:12/8
L:1/8
Q:3/8=96
K:C
V:1 clef=treble
V:2 clef=bass
V:1
"C7"z3 [EGc]3 z3 [EG_B]3 | "F7"z3 [FAc]3 z3 [_EAc]3 | "C"[EGc]12 |]
V:2
C,2 E, G,2 A, _B,2 A, G,2 E, | F,2 A, C2 D _E2 D C2 A, | [C,,C,]12 |]
```

---

## 2. Chord vocabulary in ABC (C major)

Close-position spellings. In context, voice them per section 3.

| Chord | Roman | ABC        | Chord | Roman  | ABC          |
| ----- | ----- | ---------- | ----- | ------ | ------------ |
| C     | I     | `[CEG]`    | D7    | V7/V   | `[D^FAc]`    |
| Dm    | ii    | `[DFA]`    | E7    | V7/vi  | `[E^GBd]`    |
| Em    | iii   | `[EGB]`    | A7    | V7/ii  | `[A^ceg]`    |
| F     | IV    | `[FAc]`    | B     | V/iii  | `[B^d^f]`    |
| G     | V     | `[GBd]`    | C7    | V7/IV  | `[CEG_B]`    |
| Am    | vi    | `[Ace]`    | Fm    | iv     | `[F_Ac]`     |
| Bdim  | vii°  | `[Bdf]`    | Bb    | ♭VII   | `[_Bdf]`     |
| G7    | V7    | `[GBdf]`   | Eb    | ♭III   | `[_EG_B]`    |
| C/G   | I6/4  | `G,` + `[CEG]` | Db/F | N6 (♭II6) | `F,` + `[F_A_d]` |
| C+    | I+    | `[CE^G]`   | —     | It+6   | `_A,` + `[c^f]` (A♭–C–F♯)      |
|       |       |            | —     | Fr+6   | `_A,` + `[cd^f]` (A♭–C–D–F♯)   |
|       |       |            | —     | Ger+6  | `_A,` + `[c_e^f]` (A♭–C–E♭–F♯) |

Triads without a letter suffix are major, `m` minor. V/V, V/vi, V/ii are the same as their sevenths
minus the top note (`[D^FA]`, `[E^GB]`, `[A^ce]`).

**Augmented sixths: always spell the upper note as ♯4 (F♯ in C), never ♭5 (G♭).** It resolves up
to 5. These chords get **no chord symbol**, only the annotation (`"_Ger+6"`): a symbol such as
`"Ab7"` would declare G♭ and contradict the spelling. Write `"Ab7"` only when the same sound is a
real dominant (Treatment 2 in `theory/07`, respelled with G♭).

```abc
X:1
T:Chord gallery
M:4/4
L:1/4
K:C
"C""_I"[CEG]2 "Dm""_ii"[DFA]2 | "Em""_iii"[EGB]2 "F""_IV"[FAc]2 | "G""_V"[GBd]2 "Am""_vi"[Ace]2 | "Bdim""_vii°"[Bdf]2 "G7""_V7"[GBdf]2 |
"D7""_V7/V"[D^FAc]2 "E7""_V7/vi"[E^GBd]2 | "A7""_V7/ii"[A^ceg]2 "B""_V/iii"[B^d^f]2 | "Fm""_iv"[F_Ac]2 "Bb""_bVII"[_Bdf]2 | "Eb""_bIII"[_EG_B]2 "Db/F""_N6"[F_A_d]2 |
"C+""_I+"[CE^G]2 "_It+6"[_Ac^f]2 | "_Fr+6"[_Acd^f]2 "_Ger+6"[_Ac_e^f]2 | "C/G""_I6/4"[Gce]2 "C""_I"[CEGc]2 |]
```

---

## 3. Progression examples (keyboard style)

Keyboard style per `theory/01`: right hand = three upper voices (tenor, alto, soprano) in one chord,
left hand = the bass alone. No parallel 5ths/8ves; leading tone up, chordal 7th down by step;
common tones held; chromatic alterations stay in one voice (no cross relations). The V7 bass drops
an octave (`G,` → `G,,`). All examples were checked voice by voice.

### 1. Authentic cadence: I–IV–I6/4–V7–I (soprano 8–8–8–7–8)

```abc
X:1
T:Authentic cadence
M:4/4
L:1/4
K:C
V:1 clef=treble
V:2 clef=bass
V:1
"C"[EGc] "F"[FAc] "C/G"[EGc] "G7"[FGB] | "C"[EGc]4 |]
V:2
"_I"C, "_IV"F, "_I6/4"G, "_V7"G,, | "_I"C,4 |]
```

V7 → I: B up to C, F down to E, G held. The V7 omits its 5th so that the final I is complete.

### 2. Deceptive cadence: I–IV–I6/4–V7–vi

```abc
X:1
T:Deceptive cadence
M:4/4
L:1/4
K:C
V:1 clef=treble
V:2 clef=bass
V:1
"C"[EGc] "F"[FAc] "C/G"[EGc] "G7"[DFB] | "Am"[CEc]4 |]
V:2
"_I"C, "_IV"F, "_I6/4"G, "_V7"G,, | "_vi"A,,4 |]
```

V7 → vi: the 3rd of vi is doubled (C4, C5). If G4 held and moved to A4 over the bass G → A, you
would get parallel octaves; this voicing avoids them.

### 3. Secondary dominant into deceptive cadence: I–IV–I6/4–V7/vi–vi (soprano 8–8–8–9–8)

```abc
X:1
T:V7 of vi
M:4/4
L:1/4
K:C
V:1 clef=treble
V:2 clef=bass
V:1
"C"[EGc] "F"[FAc] "C/G"[EGc] "E7"[E^Gd] | "Am"[EAc]4 |]
V:2
"_I"C, "_IV"F, "_I6/4"G, "_V7/vi"E, | "_vi"A,4 |]
```

G → G♯ stays in the alto (no cross relation). G♯ up to A, the 7th D down to C, E held.

### 4. Minor iv: I–iv–I6/4–V7–I

```abc
X:1
T:Minor iv
M:4/4
L:1/4
K:C
V:1 clef=treble
V:2 clef=bass
V:1
"C"[EGc] "Fm"[F_Ac] "C/G"[EGc] "G7"[FGB] | "C"[EGc]4 |]
V:2
"_I"C, "_iv"F, "_I6/4"G, "_V7"G,, | "_I"C,4 |]
```

A♭ is reached from G and returns to G in the alto; no A♮ appears nearby.

### 5. German augmented sixth: I–IV–I6/4–Ger+6–I6/4–V7–I

```abc
X:1
T:German sixth
M:4/4
L:1/4
K:C
V:1 clef=treble
V:2 clef=bass
V:1
"C"[EGc] "F"[FAc] "C/G"[EGc] [_E^Fc] | "C/G"[EGc] "G7"[FGB] "C"[EGc]2 |]
V:2
"_I"C, "_IV"F, "_I6/4"G, "_Ger+6"_A, | "_I6/4"G, "_V7"G,, "_I"C,2 |]
```

The augmented sixth A♭3–F♯4 expands outward to G3–G4. E♭ rises to E♮ in the same voice, so A♭–E♭
never moves in parallel 5ths to G–D. This is why Ger+6 resolves to I6/4 rather than straight to V.

### 6. Pivot-chord modulation C → G (iii = vi)

```abc
X:1
T:Pivot to G
M:4/4
L:1/4
K:C
V:1 clef=treble
V:2 clef=bass
V:1
% bar 1: set up C (I-iii-V-I); bar 2: same pivot, then V7 of G
"C"[EGc] "Em"[EGB] "G"[DGB] "C"[EGc] | "C"[Gce] "Em"[GBe] "D7"[Ac^f] "G"[GBg] |
M:4/4
K:G
!fermata!"G"[GBd]4 |]
V:2
"_I"C, "_iii"E, "_V"G, "_I"C, | "_I"C, "_iii = vi"E, "_G: V7"D, "_I"G,, |
M:4/4
K:G
"_I"G,,4 |]
```

### 7. Common-tone modulation C → A♭ (melody C becomes the 3rd of A♭)

```abc
X:1
T:Common tone to Ab
M:4/4
L:1/4
K:C
V:1 clef=treble
V:2 clef=bass
V:1
"C"[EGc] "F"[FAc] "C/G"[EGc] "G7"[FGB] |
M:4/4
K:Ab
% in Ab, bare E B A D are Eb Bb Ab Db
"Abadd9"[EBc]2 "Db"[FAd] "Eb7"[EGd] | "Ab"[EAc]4 |]
V:2
"_I"C, "_IV"F, "_I6/4"G, "_V7"G,, |
M:4/4
K:Ab
"_Ab: I(add9)"A,,2 "_IV"D, "_V7"E,, | "_I"A,,4 |]
```

The soprano C5 is held across the seam while V7 of C goes to A♭(add9). The added 9th (B♭) softens
the shift, as `theory/06` recommends.

---

## 4. Key signatures (`K:` values)

| Sharps/flats | Major | Minor | Sharps/flats | Major | Minor |
| ------------ | ----- | ----- | ------------ | ----- | ----- |
| 0            | `C`   | `Am`  | 1♭           | `F`   | `Dm`  |
| 1♯           | `G`   | `Em`  | 2♭           | `Bb`  | `Gm`  |
| 2♯           | `D`   | `Bm`  | 3♭           | `Eb`  | `Cm`  |
| 3♯           | `A`   | `F#m` | 4♭           | `Ab`  | `Fm`  |
| 4♯           | `E`   | `C#m` | 5♭           | `Db`  | `Bbm` |
| 5♯           | `B`   | `G#m` | 6♭           | `Gb`  | `Ebm` |
| 6♯           | `F#`  | `D#m` | 7♭           | `Cb`  | `Abm` |
| 7♯           | `C#`  | `A#m` |              |       |       |

Modes: `K:D dor`, `K:E phr`, `K:F lyd`, `K:G mix`, `K:A aeo`. **(toolchain)** Avoid `loc`:
music21 reads `K:B loc` as 5 sharps. Write Locrian as the matching major signature (`K:C`) with a
`%` comment. Minor keys use the natural-minor signature; write the raised 7th explicitly every time
(`^G` in `K:Am`).

---

## 5. Analysis annotation pattern

On each chord, the chord symbol goes on the right-hand chord and the Roman numeral goes as an
annotation on the bass note: `"E7"[E^Gd]` over `"_V7/vi"E,`. In a single-voice sketch, stack both:
`"E7""_V7/vi"[E^GBd]`. Mark key areas inside the annotation (`"_G: V7"`, `"_iii = vi"`). Put longer
reasoning in `%` comment lines just before the bar they describe:

```abc-fragment
% MODULATION C -> Ab by common tone: C (1 in C) becomes 3 of Ab; chromatic mediant
```

---

## 6. Common mistakes (check before emitting)

1. **Bar sums.** Add up every bar against `M:` and `L:`. With `L:1/8` a 4/4 bar is 8 units; a 6/8
   or 12/8 bar is 6 or 12. A `(3` triplet of ♪ counts as 2. `c>d` counts as 2. Grace notes count 0.
2. **Voice bars differ.** RH and LH must have the same number of bars and the same total per bar.
   Count `|` in each voice.
3. **Accidentals.** Repeat the accidental on every altered note, including after ties. Use `=` to
   cancel. Remember the key signature (in `K:D`, `F` is already F♯; `^F` is redundant, `=F` is
   F♮).
4. **Octaves.** `C` is middle C, `c` is an octave above. The LH bass usually sits in `C,`–`C` and
   the RH in `G`–`a`. One missing comma moves a bass note into the tenor.
5. **Spelling.** Use the spelling that matches the chord's function (G♯ in E7, F♯ in Ger+6, D♭ in
   N6), not whatever is easiest to type.
6. **Quoted strings.** Plain quotes must be real chord symbols. Roman numerals and words take `_` or
   `^`.
7. **Unsupported syntax.** No inline `[K:]`/`[M:]`/`[V:]`, no lone mid-piece `K:` or `M:` line
   (always the `M:` + `K:` pair), no returning to an earlier voice, no
   single-letter decorations, no hairpins, no `K:... loc`, no mixed lengths inside `[...]`.
8. **Voice leading.** Before writing each chord, check every voice pair against the previous chord
   for parallel 5ths/8ves, resolve the leading tone and the 7th, and keep chromatic notes in one
   voice.
9. **Endings.** Finish every voice with `|]`. Repeats and endings must be identical in both voices.

---

## 7. Output contract (paste into a system prompt)

```abc-fragment
Emit exactly one ABC tune in a ```abc block, in this shape:

X:1
T:<title>
M:<meter>
L:1/8
Q:1/4=<bpm>
K:<key>
V:1 clef=treble name="RH"
V:2 clef=bass name="LH"
V:1
% bars 1-4
<right-hand music, 4 bars per line, every bar complete>
V:2
% bars 1-4
<left-hand music, same bars, same durations>

Rules: header order as shown, K: last. All of V:1, then all of V:2; never return to a voice.
Accidental on every altered note, every time; `=` to cancel. Chord symbols as plain "G7";
Roman numerals as "_V7". Key or meter changes as an M: line plus a K: line, at a barline,
in both voices. Decorations as !trill! etc. End both voices with |].
```
