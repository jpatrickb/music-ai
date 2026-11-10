# Music Theory Compendium

## A Reference for Tonal Harmony, Chromatic Techniques, and Sheet Music Composition

> **Source:** BYU MUSIC 264/265, Keyboard Foundations 1 & 2 (Dr. Scott Holden, Winter 2025–2026)
> **Purpose:** Reference for human study and for LLM composition/arranging in tonal harmony. These
> files are notation-neutral (prose + Roman numerals); encoding lives in [`../encoding/`](../encoding/)

---

## How to Use This Compendium

### For Human Study

Read the files in numbered order. Each builds on the previous. The dependency graph is:

```
01-voice-leading-fundamentals
    ↓
02-cadences-and-substitutions
    ↓
03-secondary-dominants
    ↓
04-borrowed-chords-modal-mixture
    ↓
05-pivot-chord-modulation
    |
    ↓
06-common-tone-modulation
    ↓
07-augmented-sixth-chords
    ↓
08-composition-techniques (can be read anytime after 01)
```

### For LLM Generation

- Files 01–02 define the foundational rules that constrain all harmony generation
- Files 03–07 provide the full vocabulary of chromatic harmony with Roman numeral formulas
- File 08 addresses large-scale compositional structure
- Pair these with **one** encoding reference from `../encoding/` (ABC or `**kern`), which spells
  every chord type and progression in this compendium as a fully voiced, parser-validated example

---

## Contents

| File                                                                       | Topic                  | Key Concepts                                                                                 |
| -------------------------------------------------------------------------- | ---------------------- | -------------------------------------------------------------------------------------------- |
| [01-voice-leading-fundamentals.md](01-voice-leading-fundamentals.md)       | Voice Leading          | Keyboard style, parallel motion rules, cross relations, diatonic triads                      |
| [02-cadences-and-substitutions.md](02-cadences-and-substitutions.md)       | Cadences               | I–IV–I⁶₄–V7–I, deceptive cadence, deceptive cadence principle                                |
| [03-secondary-dominants.md](03-secondary-dominants.md)                     | Secondary Dominants    | V/x construction, leading tone requirement, augmented triads, implied leading tone           |
| [04-borrowed-chords-modal-mixture.md](04-borrowed-chords-modal-mixture.md) | Modal Mixture          | Minor iv, ♭VII, ♭III, Schubert techniques, cross relation warnings                           |
| [05-pivot-chord-modulation.md](05-pivot-chord-modulation.md)               | Pivot Chord Modulation | iii method (±2 steps), minor iv method (any distance), 8-chord framework, Beethoven examples |
| [06-common-tone-modulation.md](06-common-tone-modulation.md)               | Common-Tone Modulation | Single pitch pivot, chromatic mediant, enharmonic equivalence, Schumann/Bill Evans           |
| [07-augmented-sixth-chords.md](07-augmented-sixth-chords.md)               | Augmented Sixth Chords | Italian/French/German, Neapolitan, 3 treatments, modulation by ½ step and M3                 |
| [08-composition-techniques.md](08-composition-techniques.md)               | Composition Techniques | Descant writing, pedal point (tonic vs. dominant), introductions, motivic development        |
---

## Quick Reference: Roman Numeral Vocabulary

### Diatonic chords (major key)

```
I    ii   iii   IV   V   V7   vi   vii°
```

### Chromatic/Borrowed chords

```
iv          Minor subdominant (borrowed from parallel minor)
♭VII        Major triad on lowered 7th degree
♭III        Major triad on lowered 3rd degree
♭II / N     Neapolitan — major triad on lowered 2nd degree (♭II⁶)
```

### Dominant-function chords

```
V7/x        Secondary dominant (dominant 7th of chord x)
vii°/x      Secondary leading-tone chord
It⁺⁶        Italian Augmented Sixth
Fr⁺⁶        French Augmented Sixth
Ger⁺⁶       German Augmented Sixth (enharmonic = dominant 7th)
```

### Modulation chords

```
PC          Pivot chord (label used in pivot-chord modulation)
[Ger⁺⁶]*   Asterisk = reinterpreted enharmonically as V7 (or vice versa)
```

---

## Quick Reference: Cadential Formulas

### Basic authentic cadence

```
I  —  IV  —  I⁶₄  —  V7  —  I
```

### With secondary dominant (deceptive)

```
I  —  IV  —  I⁶₄  —  V7/vi  —  vi
```

### With borrowed chords

```
I  —  iv   —  I⁶₄  —  V7  —  I           (minor iv)
I  —  ♭VII —  V7   —  I                   (♭VII → V → I)
I  —  ♭III —  V(9) —  I                   (♭III → V → I)
```

### With augmented sixth

```
I  —  IV  —  I⁶₄  —  Ger⁺⁶  —  I⁶₄  —  V7  —  I
```

### Neapolitan

```
I  —  IV  —  ♭II⁶  —  I⁶₄  —  V7  —  I
```

---

## Quick Reference: Modulation Decision Tree

```
Distance on circle of fifths?
  1–2 steps → iii method (see 05)
  3–6 steps → minor iv method (see 05)
  6 steps (tritone) → not possible with these methods alone

Direction?
  Clockwise (sharps):
    iii method → use old key's iii
    minor iv   → use new key's minor iv
  Counterclockwise (flats):
    iii method → use new key's iii
    minor iv   → use old key's minor iv

Special modulations:
  ½ step up    → Ger⁺⁶ → reinterpret as V7 of new key
  ½ step down  → V7 → reinterpret as Ger⁺⁶ of new key
  M3 up        → chord7 → treat as Ger⁺⁶
  Dramatic/remote → common-tone modulation (see 06)
```

---

## Core Principles (Universal Rules)

These rules apply throughout all techniques:

1. **No parallel fifths or octaves** — ever
2. **The leading tone of the target chord must be present** for dominant function
3. **Never create cross relations** when adding chromatic chords
4. **Resolve the augmented sixth outward by half step** — always
5. **I⁶₄ before I at cadences** creates maximum tension before resolution
6. **Use chromatic devices sparingly** — strong effects lose power through overuse
7. **Match harmonic color to text/emotion** — minor and chromatic chords suit struggle/longing;
   major suits joy
8. **Add the 9th** to smooth over strong chromatic harmonic shifts
9. **Minimal voice movement** — prefer common tones and stepwise motion between chords
10. **Always take the shortest path** on the circle of fifths when choosing modulation direction

---

## Composer and Work References

| Composer    | Work                          | Technique illustrated                              |
| ----------- | ----------------------------- | -------------------------------------------------- |
| Schubert    | "Der Hirt auf dem Felsen"     | Minor iv as pivot chord, third-relation modulation |
| Beethoven   | Op. 110, A♭ Major Sonata      | Minor iv pivot (A♭ → E)                            |
| Beethoven   | Op. 10 No. 2, F Major Sonata  | Minor iv corrects "wrong" recapitulation key       |
| Beethoven   | Op. 28 "Pastorale," D Major   | Minor iv delays recapitulation                     |
| Schumann    | "Widmung" Op. 25 No. 1        | Common-tone modulation A♭ → E, text painting       |
| Rachmaninov | Piano Concerto No. 2, 2nd mvt | Minor iv chord in major context                    |
| Bach        | St. John Passion, opening mvt | Dominant pedal point                               |
| Bach        | C Major Prelude, WTC          | Dominant pedal point, delayed resolution           |
| Chopin      | Nocturne Op. 9 No. 1          | Sustained bass pedal point                         |
| Debussy     | _Voiles_, Préludes Book I     | Tonic pedal, whole-tone/pentatonic                 |
| Wagner      | _Das Rheingold_ Overture      | Extended tonic pedal point                         |
| Gounod/Bach | _Ave Maria_                   | Descant above existing melody                      |
| Bill Evans  | "Young and Foolish"           | Common-tone modulation C → A♭                      |
| Bill Evans  | "Peace Piece"                 | Tonic pedal point, modal vamp                      |
