# AGENTS.md

Guidance for coding agents (Claude Code, Codex, etc.) working in this repo. `CLAUDE.md` is a symlink to this file; edit `AGENTS.md` only.

## Hard rules

- **Never make git commits.** Not `git commit`, not amend, not anything that writes a commit or pushes. I make all commits myself. Staging, showing diffs, and suggesting a commit message are fine.
- **Never publish the local-only material.** `notes/` and `research/` are gitignored on purpose: personal notes, plans, and copyrighted paper PDFs. Don't copy their contents into tracked files (README, experiment write-ups, code comments) without being asked, and don't un-ignore them.
- **The repo is public, and it's written in my voice.** Tracked prose is first person from me
  ("I judged…", "my rules"), never "the owner". No secrets, tokens, or personal details in tracked
  files; my dictated comments and rating notes stay under gitignored `data/feedback/`. API keys
  (W&B, Hugging Face) go in `.env`, which is gitignored.

## What this project is

A solo learning-and-research project on AI for music, done in public. I'm a strong
software engineer and an ML beginner; this is a learning project first. When explaining ML
concepts, be precise and concrete, and connect them to the code being written. Don't hand-wave,
and don't silently pick a design choice that's meant to be an experiment.

The repo is general music-AI experiments, organised in tracks (goals and stages in
[`ROADMAP.md`](ROADMAP.md)). Generation is the current focus; OMR and audio transcription are
part of the project too, not side projects:

- **Generation (current focus).** LLM-written piano arrangements and pieces in `**kern`/ABC: the goal
  is musically advanced arrangements of known songs (hymns, Christmas, pop) and music for ballet
  classes, eventually from an open-weight model fine-tuned on my feedback. Context docs
  live in `experiments/generation/`, the checkers (`validate_notation`, `harmony_check`,
  `playability_check`) in `src/music_ai/`; each run is an `experiments/NNN-gen-*` folder.
  - **My blind judgment at the piano is the measure.** Automatic checks catch errors;
    corpus statistics describe style and are never generation targets.
  - **Every judged output goes into `feedback/`** (`music_ai.feedback`): generations with their
    brief, context, model and commit; ratings; preferences; corrected versions with the original
    kept.
  - Copyrighted music (pop songs, modern arrangers, most corpus encodings) is referenced by file
    and bar range or kept under gitignored paths, never committed.
- **OMR.** Score image → symbolic notation. Older notes in `notes/` frame it as
  choral-focused; that framing is superseded: the scope is general printed sheet music.
- **Audio transcription.** Recording → symbolic notation. Not yet scoped.

### OMR technical direction

Technical direction, per the literature (Legato, Legato 2, Transcoda, SMT):

- **Architecture**: pretrained vision encoder → autoregressive transformer decoder → text encoding of the score.
- **Output format**: ABC or normalized `**kern` (still an open experiment). Never train the model to emit MusicXML or MIDI directly; those are conversion targets.
- **Validity**: grammar-constrained decoding (logit masking), canonical normalization of training targets, and mechanical validation with a real parser (`music21`, `verovio`).
- **Data curriculum**: Camera-PrIMuS → GrandStaff → rendered OpenScore Lieder → real photos of printed scores (any instrumentation). Synthetic rendering (Verovio / MuseScore) plus augmentation is the main data strategy.
- **Evaluation**: build the eval harness before the training harness. Use OMR-NED (Sheet Music Benchmark) and CER; don't invent metrics.
- **Baseline to beat**: Audiveris on real-world sheet music photos and scans.

Open questions to treat as experiments, not decisions: backbone (frozen encoder + trained decoder vs VLM fine-tune vs from scratch), and ABC vs `**kern`.

## Layout

| Path | Tracked | Purpose |
|---|---|---|
| `src/music_ai/` | yes | Reusable library code: datasets, tokenizers, models, decoding, metrics |
| `experiments/NNN-slug/` | yes | One folder per experiment (see below) |
| `experiments/generation/` | yes | Generation context docs (theory, styles, encoding references) and checkers |
| `feedback/` | yes | My ratings and preferences on generated music (JSONL; see its README). My written notes stay in `data/feedback/` |
| `configs/` | yes | Training and eval configs |
| `scripts/` | yes | One-off utilities: downloads, rendering, format conversion |
| `tests/` | yes | pytest |
| `data/` | no | Datasets, renders, caches |
| `checkpoints/`, `outputs/`, `runs/`, `wandb/`, `mlruns/` | no | Run artifacts |
| `notes/` | no | My lab notebook, daily notes, paper notes, gameplan, blog drafts |
| `research/` | no | Paper PDFs (arXiv IDs as filenames) |

`notes/` is my own writing. Read it for context (`notes/gameplan.md`, `notes/omr-landscape-brief.md`, and `notes/papers/` are the most useful), but don't edit it unless asked. The lab notebook (`notes/lab-notebook.md`) is written in my voice.

## Experiments

Each experiment lives in `experiments/NNN-slug/` (e.g. `001-primus-baseline/`) with a `README.md` covering:

- **Question / hypothesis**: what this run is trying to learn
- **Setup**: data, model, config file, commit hash it ran from, hardware
- **Results**: metrics, the experiment-tracker run link, and a short error analysis
- **Takeaways / next**

Model training and evaluation runs (OMR, transcription, and later fine-tuning) are logged to
**Weights & Biases** from the first such run. The prompting experiments so far (001–004) aren't:
their record is the experiment README, the committed samples, and `feedback/`. `wandb` isn't a
dependency yet; add it (`uv add wandb`) with the first run that logs. For those runs:

- Entity `jpatrickbeal-jpatrickbeal` (the account's default), project `omr-lab`, so runs land at `wandb.ai/jpatrickbeal-jpatrickbeal/omr-lab`. Set `group` to the experiment folder name (e.g. `001-primus-baseline`) so runs map back to their write-up.
- Log the full config (`wandb.init(config=...)`), the git commit hash, dataset name/version, and device. W&B records the commit automatically if the repo is clean, so note it if a run came from uncommitted code.
- Log checkpoints and processed datasets as W&B Artifacts when they'll be reused or compared; final models and datasets meant for others go to the Hugging Face Hub.
- Auth comes from `WANDB_API_KEY` in `.env` or `wandb login`; never hard-code it. Tests and quick debugging use `WANDB_MODE=disabled` (or `offline`) so they don't pollute the project.

Experiments must be reproducible from the config plus code: fixed seeds, pinned deps via `uv.lock`, and no hand-edited data in `data/` without a script that produces it.

## Environment

- Python 3.12, managed by **uv**. Use `uv add <pkg>` to add dependencies (`uv add --dev` for tooling) and `uv run <cmd>` to run anything. Don't use bare `pip`.
- Local hardware: Apple M2 Pro, 16 GB unified memory. Use PyTorch's `mps` device locally and fall back to `cpu`; keep code device-agnostic (`cuda` / `mps` / `cpu`) so the same code runs on rented cloud GPUs.
- The laptop is for data tooling, debugging, and small models (PrIMuS-scale). Larger runs go to a rented GPU, so keep training entry points scriptable and headless.

## Commands

```sh
uv sync                 # install deps
uv run pytest           # tests
uv run ruff check .     # lint
uv run ruff format .    # format
```

## Conventions

- Library code in `src/music_ai/`, imported by scripts and experiments. Don't copy code between experiment folders.
- Type hints on public functions. Small, testable functions for tokenization, normalization, and metrics: these are where silent bugs ruin results, so they get unit tests.
- Downloaded datasets are untrusted input: put them under `data/` and never execute code from them.
