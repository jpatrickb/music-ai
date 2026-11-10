# Pivot Chord Modulation

> **Source context:** BYU MUSIC 264/265, Keyboard Foundations 1 & 2 (Dr. Scott Holden)
> **Prerequisite:** [01-voice-leading-fundamentals.md](01-voice-leading-fundamentals.md),
> [04-borrowed-chords-modal-mixture.md](04-borrowed-chords-modal-mixture.md)

---

## Definition

A **pivot chord** is a chord that is diatonic in both the old key and the new key, functioning as a
"doorway" between them. It functions as neither I (tonic) nor V (dominant) in either key — it sits
in the harmonic middle ground, allowing the ear to reinterpret the harmonic context without a
jarring break.

**Contrast with common-tone modulation:** A pivot chord is a shared _harmony_ (full chord); a
common-tone is only a shared _pitch_. See
[06-common-tone-modulation.md](06-common-tone-modulation.md).

---

## The Eight-Chord Modulation Framework

All pivot-chord modulations in this system use an eight-chord skeleton:

```
GROUP 1 (set up old key):    I  —  [PC]  —  V  —  I
GROUP 2 (move to new key):   I  —  [PC]  —  V7(new)  —  I(new)
```

Where `[PC]` = the pivot chord, functioning in both keys.

**Key principle:** The same four-chord shape appears twice. In Group 1, the pivot chord passes
without consequence. In Group 2, the same chord is reinterpreted and leads to the new key's dominant
seventh, arriving at the new tonic.

---

## Part I: The Minor iii Chord — Modulating ±2 Steps on the Circle of Fifths

### Which iii chord to use

The iii chord (minor triad on scale degree 3) is the pivot for modulations up to two steps away on
the circle of fifths.

**The universal rule for iii:** Always use the iii chord belonging to whichever of the two keys is
**most counterclockwise (most toward the flat side)** on the circle of fifths.

**Practical shortcuts:**

**One click clockwise (keys a perfect fifth apart):** Stack the two tonic notes in perfect fifths.
The iii chord is a major third above the lower (more flat-side) tonic.

```
C to G:   lower tonic = C → iii = E minor (major third above C)
F to C:   lower tonic = F → iii = A minor (major third above F)
Ab to Eb: lower tonic = Ab → iii = C minor (major third above Ab)
```

**Two clicks clockwise (keys a major second apart) — the "1-2-3 Method":** The three tonic-like
notes form three consecutive whole steps.

```
C to D:   C–D–E → iii chord = E minor
G to A:   G–A–B → iii chord = B minor
Bb to C:  Bb–C–D → iii chord = D minor
```

**Two clicks counterclockwise (keys a major second apart):** Apply the flat-side rule: use the iii
of the more counterclockwise key.

```
C to Bb:  more flat-side key = Bb → iii = D minor
G to F:   more flat-side key = F → iii = A minor
```

### Direction-specific rule summary

| Direction                       | Which key's iii? | Example (C major)               |
| ------------------------------- | ---------------- | ------------------------------- |
| Clockwise (toward sharps)       | Old key's iii    | C → D: use E minor (iii of C)   |
| Counterclockwise (toward flats) | New key's iii    | C → Bb: use D minor (iii of Bb) |

### Range

The iii-chord method can reach **±2 steps** on the circle of fifths. Beyond that, use the minor iv
method.

### Example: C Major → D Major (one step clockwise)

```
Group 1:  C major  —  E minor  —  G major  —  C major
Group 2:  C major  —  E minor  —  A7        —  D major
          (I)          (iii/I)   (V7/D)       (I new)

In D major: E minor = ii of D major (the pivot reinterpretation)
```

### Example: C Major → G Major (one step clockwise)

```
Group 1:  C major  —  E minor  —  G major  —  C major
Group 2:  C major  —  E minor  —  D7        —  G major

In G major: E minor = vi of G major (the pivot reinterpretation)
```

---

## Part II: The Minor iv Chord — Modulating Anywhere on the Circle of Fifths

### Why a New Pivot is Needed

The iii chord can only reach ±2 steps. To modulate further, the **minor iv** chord (borrowed from
the parallel minor) serves as the pivot. Because both major and minor keys share the same dominant,
the minor iv chord is interpretable in a wide variety of tonal contexts.

**Scope:** Can reach any key except the tritone (exactly 6 steps away, i.e., the diametrically
opposite key).

### Which minor iv chord to use

**The direction rules for minor iv:**

| Direction                       | Mnemonic                        | Which key's minor iv? | Example (C major)                         |
| ------------------------------- | ------------------------------- | --------------------- | ----------------------------------------- |
| Clockwise (toward sharps)       | "Things that are sharp are new" | New key's minor iv    | C → E: use A♭ minor (minor iv of E major) |
| Counterclockwise (toward flats) | "Things that are flat are old"  | Old key's minor iv    | C → Ab: use F minor (minor iv of C major) |

**Always take the shortest path** on the circle of fifths. If the two keys are equidistant, choose
the direction that makes more musical sense in context.

```
Ab to B:
  Clockwise path: Ab → Eb → Bb → F → C → G → D → A → E → B = 9 steps
  Counterclockwise: Ab → Db → Gb → B = 3 steps
  → Use counterclockwise → old key's minor iv (Db minor / C# minor)
```

### Example: C Major → A♭ Major (4 steps counterclockwise)

```
Group 1:  C  —  F minor  —  G7   —  C
Group 2:  C  —  F minor  —  Eb7  —  Ab major

In Ab major: F minor = vi of Ab major (pivot reinterpretation)
```

F minor = minor iv of C major (old key, counterclockwise rule ✓)

### Example: C Major → E Major (4 steps clockwise)

```
Group 1:  C  —  Ab minor  —  G7   —  C
Group 2:  C  —  Ab minor  —  B7   —  E major

In E major: Ab minor (= G# minor) = iii of E major (pivot reinterpretation)
```

A♭ minor / G# minor = minor iv of E major (new key, clockwise rule ✓)

### Examples table

| Old key | New key | Direction        | Minor iv chord             | Roman numeral in new key |
| ------- | ------- | ---------------- | -------------------------- | ------------------------ |
| F       | D       | Clockwise        | G minor (iv of D)          | iv becomes iv in new key |
| D       | F       | Counterclockwise | G minor (iv of D, old key) | G minor = ii of F        |
| C       | Eb      | Counterclockwise | F minor (iv of C)          | F minor = ii of Eb       |
| A       | Bb      | Counterclockwise | D minor (iv of A)          | D minor = iii of Bb      |
| B       | C       | Counterclockwise | E minor (iv of B)          | E minor = iii of C       |
| Eb      | D       | Clockwise        | G minor (iv of D)          | iv of D (new)            |

---

## Part III: Direction Asymmetry and Practical Tendencies

**Counterclockwise modulations sound weaker.** One-step flat-side modulations (e.g., C major → F
major) sound less directed and somewhat "lame" in short-form contexts. Large-scale structural
modulations in Baroque and Classical music are almost always **clockwise** (toward the sharp side).

- Baroque dance suite: tonic → dominant (one step clockwise) is normative
- Sonata form: tonic → relative major or dominant
- Most "interesting" modulations to remote keys go clockwise or use specific dramatic devices

---

## Part IV: Beethoven's Use of the Minor iv Pivot — Recapitulations

Beethoven uses the minor iv pivot chord in **recapitulations** of sonata-form movements, either to
escape an unexpected tonal destination or to delay the return to the home key.

### Example 1: Op. 110 in A♭ Major — Escaping to E Major

After establishing the recap in A♭ major, Beethoven modulates to E major via the minor iv:

```
Ab major:    I  —  Db minor (minor iv)  —  B7  —  E major
                   ↑ C# minor enharmonically
```

- Direction: A♭ to E = counterclockwise (3 steps) → use **old key's** minor iv
- A♭ minor natural minor contains D♭ minor = iv of A♭ major ✓
- D♭ minor = C# minor enharmonically = iii of E major (pivot reinterpretation)

### Example 2: Op. 10 No. 2 in F Major — Correcting the "Wrong" Recapitulation

Beethoven deliberately enters the recap in D major instead of F major, then corrects:

```
D major established  →  G minor (minor iv of D)  →  C7  →  F major
```

- G minor = minor iv of D major (old key, counterclockwise to F major) ✓
- G minor = ii of F major (pivot reinterpretation) ✓
- C7 = V7 of F major → arrives at correct tonic

### Example 3: Op. 28 "Pastorale" in D Major — Delaying the Recap

Development ends in F# major; recap is in D major:

```
F# major  →  B minor (minor iv of F#)  →  A7  →  D major
```

- F# to D = counterclockwise (3 steps) → use **old key's** minor iv
- F# natural minor contains B minor ✓
- B minor = vi of D major (pivot reinterpretation) ✓

---

## Circle of Fifths Reference (Clock Metaphor)

```
         C (12:00)
    F  ←           → G
(11:00)             (1:00)
  Bb                  D
(10:00)             (2:00)
   Eb                  A
(9:00)              (3:00)
    Ab              E
(8:00)             (4:00)
      Db       B
        (7:00) (5:00)
           Gb/F#
           (6:00)
```

- **Clockwise** = toward sharps (each step adds one sharp / removes one flat)
- **Counterclockwise** = toward flats (each step adds one flat / removes one sharp)
- Keys are related by perfect fifth in adjacent positions

---

## Quick Modulation Decision Tree

```
1. What is the old key? What is the new key?
2. How many steps apart on the circle of fifths?
   a. 1–2 steps: can use iii chord method
   b. 3–6 steps: must use minor iv method
   c. 6 steps: tritone — not achievable with this system
3. Which direction is shorter (fewest steps)?
4. Apply direction rule:
   - iii method:      clockwise = old key's iii; counterclockwise = new key's iii
   - minor iv method: clockwise = new key's minor iv; counterclockwise = old key's minor iv
5. Build the 8-chord framework:
   Group 1: I — [PC] — V7 — I (old key)
   Group 2: I — [PC] — V7(new) — I(new)
```
