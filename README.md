# squillo-lab

Experiments that ground squillo's specification in evidence. Code is allowed
here, and is the point. Nothing here ships: `squillo` holds the specification,
and this repo holds what we measured to write it.

Everything traces to [`squillo/VISION.md`](https://github.com/ZerNox/squillo/blob/main/VISION.md).
An experiment that answers no question the vision raises does not belong.

## How an experiment works

One folder per experiment: `experiments/E-nnn-short-name/`.

| File | Holds |
| :--- | :--- |
| `README.md` | Question, vision section served, hypothesis, protocol, **result**, status |
| `run.*` / `src/` | The code. Runnable unattended where possible, with one command in the README |
| `data/` | Inputs, each with source and licence in `data/SOURCES.md`. Large or non-redistributable data is fetched by script, not committed |
| `results/` | Outputs: numbers, plots, audio examples. Small, committed, reproducible from the code |

**Check inputs and measures before the full run** (squillo standing
instruction S15). Run a few unmodified real recordings first: a synthetic
input's long-term spectrum must lie within theirs, and a spectral or distance
measure must be restricted to a band where both have energy. The README
reports the check's numbers. Every synthetic input must also lie inside the
range the measure is specified for (for pitch, squillo ADR 0007's E2–C6),
and any procedure that makes the truth (alignment, segmentation) is run on
one input of every condition first (squillo L-026).

**A result is a number with its conditions.** State what was measured, on what
input, with which tool versions, and the uncertainty. "Works well" is not a
result.

**Needs a human.** Some experiments need a real microphone, a real room or a
real listener. Their README says so in the status line (`needs-human`) and
gives Joakim a protocol short enough to run in 15 minutes.

**Feeding squillo.** A squillo spec or ADR cites an experiment by ID and commit
(`squillo-lab E-002 @ <sha>`). Exact numbers in `signal` and `metrics` come
from here or from cited literature, never from nowhere.

## Tooling

- **Python via `uv`**: each experiment has its own `pyproject.toml`; run with
  `uv run`. For offline research on signals, measurement and synthesis.
- **Scores**: LilyPond from the PyPI `lilypond` wheel, as a `uv`
  dependency (E-004), compiles score text to MIDI; nothing system-wide.
- **Browsers**: Node with Playwright, driving the installed Chrome and
  Firefox. Chrome's fake audio capture (`--use-file-for-fake-audio-capture`)
  feeds a WAV file as the microphone.
- **Rust / WASM**: added when an experiment needs to test the real engine
  path; not installed yet.
- **GPU**: an Intel Arc A770M, which stands in for the remote tier and not for
  a singer's device. Read [`COMPUTE.md`](COMPUTE.md) before timing anything on
  it.

## Status

See [`INDEX.md`](INDEX.md).
