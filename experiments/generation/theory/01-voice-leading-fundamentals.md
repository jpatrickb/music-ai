# Voice Leading Fundamentals

> **Source context:** BYU MUSIC 264/265, Keyboard Foundations (Dr. Scott Holden) **Purpose:**
> Foundation for all harmonic work. Every technique in this compendium depends on these rules.

---

## Keyboard-Style Voicing

This compendium uses **keyboard style** (also called "piano style"), not chorale SATB style:

- **Left hand (LH):** One note — the bass
- **Right hand (RH):** Three notes — soprano (top), alto (middle), tenor (inner)
- The two hands together create a four-voice texture. This differs from chorale style where
  soprano/alto are in the RH and tenor/bass in the LH.

**Drill layout vs composing.** The course's cadence drills keep the bass on chord roots (except the
cadential I⁶₄) so the RH patterns can be learned in every key. That is a practice convention, not a
rule for writing music. Real pieces use inversions freely, mainly to give the bass its own line:
stepwise bass motion through I⁶, V⁶, V⁴₃, IV⁶ and passing ⁶₄ chords is common. Choose the bass as a
melody in its own right rather than defaulting to roots.

**Bass register:** Lower the LH bass an octave on V7 chords for a stronger cadential effect.

---

## The Six Voice-Leading Rules

### Rule 1: Keyboard-Style Layout

Three voices in RH, one in LH. The LH note is the bass and determines the chord's inversion; RH
voicing does not need to match it.

### Rule 2: NO Parallel Fifths or Octaves (Absolute)

Parallel perfect fifths and parallel octaves between any two voices are forbidden. This is the most
important rule — treat it as inviolable.

**What to check:** When moving from one chord to the next, verify no two voices move in the same
direction by the same interval if that interval is a fifth or octave.

### Rule 3: Contrary or Oblique Outer-Voice Motion

The soprano and bass should generally move in contrary motion (opposite directions) or oblique
motion (one voice stays, the other moves). This is the primary mechanism for avoiding parallel
octaves and fifths.

- **Contrary motion:** Soprano goes up, bass goes down (or vice versa)
- **Oblique motion:** One outer voice sustains while the other moves

### Rule 4: Minimal Voice Movement

When changing chords, move each voice the smallest possible distance. Prefer:

- Common tones: if a pitch appears in both chords, keep it in the same voice
- Stepwise motion (minor or major 2nd) over leaps
- Smaller leaps (3rds) over larger ones (6ths, 7ths)

### Rule 5: Soprano Starting Position

Begin the soprano on scale degree 8 (tonic) for cadential exercises. This creates predictable,
repeatable voice-leading patterns across all keys.

**Common soprano patterns over I–IV–I⁶₄–V7–I:**

- 8 – 8 – 8 – 7 – 8
- 3 – 4 – 3 – 4 – 3
- 5 – 6 – 5 – 5 – 5

### Rule 6: Inversion Determined by Bass

The bass (LH) alone decides the inversion: root in the bass is root position, the third is first
inversion, the fifth is second inversion. The RH voicing independently chooses the best spacing for
smooth inner-voice movement. These are separate decisions.

---

## Additional Voice-Leading Considerations

### Cross Relations

A **cross relation** occurs when the same pitch class appears with two different chromatic qualities
(natural vs. sharp/flat) in different voices in adjacent chords.

- **Example:** If the alto has F♮ in chord 1 and the tenor has F# in chord 2 (or vice versa), that
  is a cross relation.
- Cross relations are almost always dissonant and wrong-sounding.
- **Most common trigger:** Adding secondary dominants or borrowing chords from the parallel minor.
  Always check for cross relations when inserting chromatic alterations.
- **Fix:** Either put both chromatic versions in the same voice, or adjust the voicing to eliminate
  the conflict.

### Leading Tone Resolution

The leading tone (scale degree 7) strongly implies upward resolution to scale degree 8 (tonic). In
dominant-function chords (V, V7, vii°), the leading tone should resolve upward by half step to the
tonic whenever possible.

### Chordal Seventh Resolution

The seventh of a dominant seventh chord (scale degree 4 in V7) resolves downward by step to scale
degree 3.

### Doubling

- In root-position triads: double the root (bass note) when possible
- Avoid doubling the leading tone
- In the cadential I⁶₄: double the bass (scale degree 5) — it appears in both soprano and bass

---

## The Standard Cadential Progression

The foundation of all harmonic work in this system:

```
I  —  IV  —  I⁶₄  —  V7  —  I
```

**Function of each chord:**

| Chord | Scale degrees in RH            | Function                                               |
| ----- | ------------------------------ | ------------------------------------------------------ |
| I     | 1, 3, 5 (various arrangements) | Tonic — home                                           |
| IV    | 1, 4, 6                        | Subdominant — pre-dominant                             |
| I⁶₄   | 5, 1, 3 (bass = 5)             | Cadential 6/4 — dominant (V with 6–5, 4–3 suspensions) |
| V7    | 2, 5, 7                        | Dominant — maximum tension                             |
| I     | 1, 3, 5                        | Tonic — resolution                                     |

**The I⁶₄ (cadential six-four):**

- The bass plays scale degree 5 (same pitch as V)
- The RH plays tones of the I chord in second inversion
- Sounds tense because the "wrong" notes (3 and 1) sit above a dominant-suggesting bass
- Always resolves to V7, then I — never used independently
- **Encoding note:** label it as a C major chord over G (chord symbol `C/G` in C major). The Roman
  numeral is spelled per format: `"_I6/4"` in ABC, `Ic` in a kern `**harm` spine (never `I64`, which
  music21 misparses). It contextually functions as tension before the dominant, not as a tonic
  arrival. See `../encoding/` for the ABC and `**kern` spellings.

---

## Diatonic Triad Quality Pattern (Major Keys)

Memorize this pattern — it applies in every major key:

| Scale Degree | Roman Numeral | Quality    |
| ------------ | ------------- | ---------- |
| 1            | I             | Major      |
| 2            | ii            | minor      |
| 3            | iii           | minor      |
| 4            | IV            | Major      |
| 5            | V             | Major      |
| 6            | vi            | minor      |
| 7            | vii°          | diminished |

**Memory shortcut:** I, IV, V = Major. ii, iii, vi = minor. vii = diminished.

---

## Triadic Scale Exercise

To internalize all keys, practice "triadic scales" — diatonic triads ascending through all seven
scale degrees, then back down:

**C major triadic scale (root position):** C–E–G → D–F–A → E–G–B → F–A–C → G–B–D → A–C–E → B–D–F →
(C–E–G)

Practice in root position, then first inversion, then second inversion in every major key.

---

## Voice Leading in Chromatic Contexts

When adding chromatic alterations (secondary dominants, borrowed chords, augmented sixths):

1. **Check for cross relations** before and after the altered chord
2. **The leading tone of the target chord must be present** for dominant function to work
3. **Augmented intervals in the voice leading** (e.g., augmented 2nds) should generally be avoided
   in inner voices
4. **The augmented sixth interval** always resolves outward by half step — both pitches expand away
   from each other to the octave
