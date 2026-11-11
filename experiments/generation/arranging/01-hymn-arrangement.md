# Arranging a song for solo piano

This page is an index, not a recipe. It lists the decisions an arrangement needs and points to
where the guidance for each lives: the theory compendium (`../theory/`, from BYU keyboard
harmony courses), the style cards (`../styles/`), and real excerpts given with the task. It
prescribes no form, progression or technique. Choose from the sources, and be able to say why
each choice serves this song.

The rules marked **(owner)** come from the owner's judgments of earlier arrangements (experiment
003); the words behind them are in `feedback/comments/003-general.md`.

The version of this page used in experiment 003 prescribed a form and a set of devices. All ten
arrangements converged on it, and the owner judged those choices poor. It is kept in git history
at commit `0cb5fb6`.

## 1. Plan before writing

Write the plan down before any notes. Each item should give a reason.

- **Style.** Which style, and which excerpts show it? Name the texture and figuration you're
  borrowing from them. See the style cards and the excerpts given with the task. Style decides
  most of the texture: settle it first. **(owner)**
- **Story.** What is each verse about, and how should it feel? Where is the emotional high
  point? With lyrics in the source (`**text` spines), read every verse.
- **Text painting.** Which harmonies, textures, registers or figures reflect specific words or
  images? This needs a reason for the effect of each device: the "harmonic function and effect"
  sections of the theory pages describe them. **(owner)**
- **Harmonic plan.** Where does harmonic colour go, which chords, and why there? Where do
  modulations go, by which method, and over how long? See section 3.
- **Texture plan.** The accompaniment for each section, and how it changes between sections.
- **Countermelody.** Optionally, a short motif of 3–4 notes that fits against the tune and can
  return, rather than a full second melody (`../theory/08-composition-techniques.md` covers
  descants). **(owner)**

## 2. The tune

- The arrangement must stay recognisable as the song. It needn't keep the melody exactly: notes
  can be changed or swapped, ornaments added, and rhythms changed, mostly by augmentation or
  diminution (stretching or compressing by a fixed ratio) rather than by rewriting them.
  **(owner)**
- **Rule of thumb (owner):** if both the melody and the harmony have been changed at the same
  place, the song has been changed. Vary one against a recognisable other.
- Where the tune goes (top, inner voice, bass) is a texture choice. See the style cards and
  excerpts.

## 3. Harmony

Choose from the compendium; don't add a chord because it is available. **(owner)** A chromatic
chord should lead somewhere and stay long enough to mean something. A secondary dominant dropped
in for a beat, or a borrowed chord that appears and vanishes, sounds like box-ticking.

| Decision | Read |
| -------- | ---- |
| Voicing, doubling, parallels, resolving sevenths and leading tones | `../theory/01-voice-leading-fundamentals.md` |
| Cadences, deceptive cadences and the deceptive-cadence principle | `../theory/02-cadences-and-substitutions.md` |
| Secondary dominants and diminished chords, and when to add one | `../theory/03-secondary-dominants.md` ("Checklist Before Adding a Secondary Dominant") |
| Borrowed chords (iv, ♭VII, ♭III): setup conditions, resolution, effect | `../theory/04-borrowed-chords-modal-mixture.md` |
| Modulation by pivot chord (iii method, minor iv method, decision tree) | `../theory/05-pivot-chord-modulation.md` |
| Modulation by common tone (no preparation needed; chromatic mediants) | `../theory/06-common-tone-modulation.md` |
| Augmented sixths and the Neapolitan; half-step and distant modulations | `../theory/07-augmented-sixth-chords.md` |
| Descants, pedal points, introductions, motivic development | `../theory/08-composition-techniques.md` |

Modulation craft **(owner)**:

- Give a key change room: preparation, an interlude, or time to move around before arriving.
  One or two bars is usually too quick.
- Delay full arrival. Use the new key's strong chords at partial strength (inverted, incomplete)
  and put off the root-position tonic, sitting in the tension of the new key.
- Non-chord tones (ninths, elevenths, thirteenths, suspensions) add tension, and voicing matters
  most in the tricky modulations (augmented sixths).
- "Hit the new key's V7 and land" is not a modulation.

Other harmony rules **(owner)**:

- Doubling priority: root, then fifth, then third, then seventh. Don't double the seventh of a
  seventh chord.
- Second-inversion (6/4) chords only as passing or cadential 6/4s, and that applies inside
  arpeggios too.
- Don't end a cadence with the chordal seventh in the melody. The seventh resolves down to the
  third of the next chord.

## 4. Texture and playability

The style and excerpts are the main guide to texture. These rules apply in any style **(owner)**:

- Vary the accompaniment, in both pattern and rhythm. A whole verse of the same eighth-note
  broken chord ("bouncing bass") is bland. Liked so far: Chopin-like stride, quarter-note
  accompaniment, triplets, running sixteenths, an octave on the first note of a triplet then the
  arpeggio, melody in octaves.
- Keep the low register open. About a fifth is the closest two notes should be down there. Put
  a dominant's seventh high, not low in the bass, where it muddies instead of creating tension.
- Leaps inside an arpeggio: not more than an octave. Never an octave (or near it) followed by
  another large leap: the hand has to cross after a big leap and can't stretch at the same time.
  When a figure covers a wide range, keep its upper notes closer together.
- Ornament with intent. Runs and fills must fit the style and lead somewhere, not decorate a
  static chord.
- Block chords in one hand within a ninth. The two hands shouldn't sit on the same notes at the
  same time.
- Pedal in kern: `*ped` starts and `*Xped` releases the sustain pedal (tandem interpretations in
  the left-hand spine).
