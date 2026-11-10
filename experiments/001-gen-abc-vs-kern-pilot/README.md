# 001: LLM generation, ABC vs `**kern` (pilot)

## Question / hypothesis

Given the same theory/style context and the same task, does an LLM produce more valid, musically
correct piano scores when its encoding reference is ABC or `**kern`?

Hypothesis (weak): ABC gives higher first-attempt syntactic validity (compact, familiar from web
data); `**kern` gives better rhythmic alignment between hands (explicit time-aligned rows) but more
spine-structure errors.

This is a **pilot**: 1 sample per cell, so it can only surface failure modes and check that the
pipeline works. It can't support a conclusion about which format is better.

## Setup

- **Generator:** Claude Code teammate agents (subscription), model `claude-opus-5-5`, one fresh
  agent per piece (no shared context between samples). Agents may only read the listed context files
  and write one output file. No code execution, so this measures first-attempt output with no
  self-validation loop.
- **Context per arm:** `experiments/generation/encoding/{abc,kern}-reference.md` (the only thing
  that differs between arms) + the task's theory/style files (identical across arms).
- **Not a clean prompt control:** agents also see the repo's `AGENTS.md` and Claude Code's own
  system prompt, and they read files instead of receiving a fixed system prompt. That confound is
  the same in both arms. A scripted API or open-weights run would remove it (planned).
- **Tasks:**

| ID  | Task                                                                                                                                                                               | Context (besides encoding ref)             |
| --- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------ |
| T1  | 8 bars, C major, 4/4, keyboard style (RH 3-note chords, LH bass). A deceptive cadence (V7–vi) at bar 4, then an authentic cadence I–IV–I⁶₄–V7–I to end. Roman-numeral analysis.    | theory/01, theory/02                       |
| T2  | 8 bars, G major, 3/4, keyboard style. Use V7/V and V7/vi, each resolving correctly; end with a PAC. Roman-numeral analysis.                                                        | theory/01, theory/03                       |
| T3  | 16 bars, A♭ major, 4/4, Romantic style (melody over arpeggiated LH). Modulate to C major by common-tone modulation around bar 8; final cadence in C uses a German augmented sixth. | theory/01, theory/06, theory/07, styles/01 |
| T4  | 12-bar blues in F, 4/4, stride piano (LH bass note / chord alternation, RH blues melody with blue notes), standard 12-bar form, swing feel.                                        | styles/03                                  |

- **Evaluation:** `validate_notation.py` (music21 parse, per-bar duration vs meter, Verovio load and
  log warnings), `harmony_check.py` (parallels, LT/7th resolution, spacing), and a manual listen /
  read of each render against the task spec.
- **Code:** uncommitted working tree on top of `c4b9e42`; the context docs, samples and checkers as
  run are committed in `2d97389`.

## Results

Run 2026-11-09. Generated pieces: `samples/{abc,kern}/T{n}.{abc,krn}`. Renders, MIDI and MusicXML
(not tracked) go in `<repo>/outputs/001-gen-abc-vs-kern-pilot/`. Not yet logged to W&B. Blind piano
judging by the owner (private page, A/B order hidden): ratings pending.

| Task | ABC valid | kern valid | Harmony check (high / low+med) | Meets task (manual)                                                     |
| ---- | --------- | ---------- | ------------------------------ | ----------------------------------------------------------------------- |
| T1   | ✓         | ✓          | 0/0 · 0/0                      | ✓ · ✓ (both end with soprano on 5, an imperfect authentic cadence)      |
| T2   | ✓         | ✓          | 0/0 · 0/0                      | ✓ · ✓                                                                   |
| T3   | ✓         | ✓          | 0/1 · 0/1                      | ✓ · ✓ (kern ties the common tone across the modulation, richer harmony) |
| T4   | ✓         | ✓          | 0/2 · 0/0                      | ✓ · ✓ (kern notates swing as triplets, ABC as straight ♪ + "Swing")     |

- **Validity: 8/8 first-attempt valid** (music21 parse, per-bar durations, cross-voice bar
  alignment, Verovio load with no logged warnings). The validator does catch errors: an extra rest
  injected into the ABC T2 copy and a deleted row in the kern T2 copy both FAIL. So these tasks
  don't separate the formats on syntax.
- **Harmony checker:** no high-severity findings. The first version raised 8 low/medium warnings on
  T3/T4, all false positives (an arpeggiated or stride LH read note by note as the bass, and a
  spacing check applied between the hands). After refining it to compare outer voices per harmonic
  unit, those are gone and 4 low warnings remain, all judged real but mild: parallel octaves between
  consecutive chord downbeats with melody notes in between (ABC T3 bar 10, kern T3 bar 2), and two
  parallel 5ths at the I7–V7/ii–ii7 turnaround in ABC T4 (normal in stride style). The table counts
  the refined checker.
- **Manual read:** every piece meets its task, with no clear voice-leading errors. Secondary
  dominants, the German sixth (spelled F♯, resolving to I⁶₄ without Mozart fifths) and the
  common-tone modulations are all handled correctly in both formats.

### Error analysis: the reference docs drive the choices

- **Cadential 6/4 → V7.** In 5 of the 6 pieces that use a cadential 6/4 (all but ABC T3; T4 has
  none), the 6th above the bass rises to the chordal 7th (E→F in C) instead of falling to the 5th
  (E→D). This is not an error: it is the keyboard-style variant behind the 3–4–3–4–3 soprano pattern
  in `theory/01`. But the textbook default (6–5, 4–3; the `theory/02` voicing table, G–C–E → F–B–D)
  never appeared, because both encoding references used only the variant (`[EGc]` → `[FGB]`) in
  their cadence examples. The generators copied the in-context examples. Lesson: the examples set
  the defaults, more than the prose does.
- **Swing (T4) is a doc asymmetry, not a format effect.** The kern reference says straight eighths
  plus a "swing" label is not machine-readable and to avoid it. The ABC reference explicitly allows
  it. The two arms followed their own docs.
- The kern primer demo also contains a voice-leading slip (the D7's inner-voice 7th, C4, leaps up
  instead of resolving to B3), found by the harmony checker.

## Takeaways / next

- The pipeline works end to end: generate → validate → harmony check → render/MIDI.
- The tasks are too easy to separate ABC from kern; both are at ceiling. Next run: harder tasks
  (longer pieces, denser textures, more voices, tuplets, mid-piece meter changes), several samples
  per cell, and a fixed system prompt (API or open-weights model) to remove the Claude Code
  confound.
- "Same musical content" in the two references has to include the same guidance, not just the same
  progressions.

## Changes to the context after this pilot

The next run uses changed context docs, so compare it against this pilot with care. Changed after
`2d97389`:

- Both encoding references: cadential 6/4 examples 1, 4 and 5 now use the default 6–5/4–3 resolution
  (`[EGc]` → `[DFB]` → `[CEc]`). Example 7 keeps the 6→7 variant, labeled, and a note explains both.
- ABC reference: swing guidance now matches kern (12/8, or a 4/4 triplet pair `(3:2:2c2d`; straight
  eighths plus a "Swing" label is to be avoided). The chord gallery is noted as a chord list, not
  voice-led music.
- kern reference: the primer demo's D7 now resolves its 7th (C4→B3).
- `theory/01`: I⁶₄ RH scale degrees corrected to 5, 1, 3. Its encoding note now spells the Roman
  numeral per format (`"_I6/4"` in ABC, `Ic` in kern).
- After the changes, both references pass the validator (20/20). The harmony checker flags only the
  ABC chord gallery (14 warnings, expected).
- Log runs to W&B (group `001-gen-abc-vs-kern-pilot`) once the eval is scripted.
