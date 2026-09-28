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

**Assert every generated input's conditions, and check every check**
(squillo standing instruction S15). Before generating an input, for a run
or for a squillo fixture, write down every condition it must meet: the
range the measure is specified for (for pitch, squillo ADR 0007's E2–C6),
every condition of the requirement a fixture serves, and, for a synthetic
or re-synthesized stand-in for voices, the range real recordings of the
same kind span (such as one singer's takes; never pooled extremes band by
band), compared only where both have energy. A condition carried over from
an earlier round or experiment is read from its code, citing the line,
never from its README's prose. The generator asserts each
condition on what it generated, with extremes computed from the output or
its exact formula, never from nominal parameters, and stops if one fails.
Any procedure that makes the truth (alignment, segmentation) runs on one
input of every condition first. **A check is itself checked before it is
trusted:** its bounds are computed in code from their source's definition,
never retyped; a tool's arrays are matched to frames by the index it
returns, never by position; and it is run once on a case it must pass and
once on a case it must fail, each known independently of the check. A
pass bar or a selection rule written before a run is a check too: it is
applied first to the reference condition that must pass it (such as clean
input on the fitting fold) and to one that must fail it. The
README reports the checks' numbers (squillo L-024, L-026, L-028, L-030,
L-031, L-032, L-034, L-036).

**Name the reference before comparing** (squillo standing instruction S16).
A check against an outside source names its reference item in advance: the
article's score block, the person's entity, the edition. It never takes the
best match among several, because a different work can match. Caches of
outside reads are keyed by the whole request (squillo L-027).

**Place every anomaly in the input's own structure** (squillo standing
instruction S17). When a known input passes through a system the lab does
not control (a browser's fake device, a looped source, a codec), the
analysis records where each anomaly falls in the input: its start, a loop
point, a file boundary. One that falls there is attributed to the input
path until a run without that structure clears it. A bracket counts as
falling there when it holds the point: its position in the input's own
time wraps, or it is longer than the loop (squillo L-032). A sign or direction
stated in a result's legend is derived from the measure's definition in the
code and checked by hand on one case (squillo L-029, L-032).

**Time the full run before starting it** (squillo standing instruction
S19). Before a run longer than a few minutes, time one item of the slowest
condition on one process, multiply out over the design and the processes,
and write the estimate in the README's command block. If the run and its
analysis do not fit well inside the session, cut the design (fewer cells,
fewer items per cell) before starting, never after (squillo L-033).

**Every claim about the code is matched to the code** (squillo standing
instruction S18). Before committing a README's check table, a docstring or
a commit message that says what the code does (a bound read from a line, a
condition asserted, a case run), match each clause to the line of the
diff or the result that makes it true. Remove or make true a clause with
none. A check with no must-fail case says so in its own row (squillo
L-032, L-035).

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
  feeds a WAV file as the microphone. The Firefox here is a snap, which
  sees neither `/tmp` nor hidden directories under home, and the worktrees
  may live under `~/.local`; give it a profile directory under
  `~/snap/firefox/common/` (E-003's `run.mjs`) and remove it afterwards.
- **Rust / WASM**: Rust stable with the `wasm32-unknown-unknown` target and
  `wasm-bindgen-cli`, in `~/.cargo`. Installed by [`prereqs.sh`](prereqs.sh),
  which the squillo runner runs before every iteration.
- **Prerequisites**: [`prereqs.sh`](prereqs.sh) installs everything the lab
  needs for the current user only, never with sudo, and skips what is present
  (`--check` only reports). An experiment that needs a new tool adds a step
  there and commits it with the experiment.
- **GPU**: an Intel Arc A770M, which stands in for the remote tier and not for
  a singer's device. Read [`COMPUTE.md`](COMPUTE.md) before timing anything on
  it.

## Status

See [`INDEX.md`](INDEX.md).
