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
- **Browsers**: Node with Playwright, driving the installed Chrome and
  Firefox. Chrome's fake audio capture (`--use-file-for-fake-audio-capture`)
  feeds a WAV file as the microphone.
- **Rust / WASM**: added when an experiment needs to test the real engine
  path; not installed yet.

## Status

See [`INDEX.md`](INDEX.md).
