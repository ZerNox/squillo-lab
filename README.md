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
(squillo standing instruction S15). The principle: nothing an experiment
generates or checks is trusted until it has been checked itself, and every
rule is in git before the data it judges. The checklist below is that
instruction in full (squillo R-15 moved it here from squillo's
`lessons.md`, where S15 now states the principle). An experiment's README
names the items it applied; a recurrence revises the item, not the
principle.

*Inputs*

- **C1.** Before generating an input, for a run or for a squillo fixture,
  write down every condition it must meet: the range the measure is
  specified for (for pitch, squillo ADR 0007's E2–C6), every condition of
  the requirement a fixture serves, and, for a synthetic or re-synthesized
  stand-in for voices, the range real recordings of the same kind span
  (such as one singer's takes; never pooled extremes band by band),
  compared only where both have energy.
- **C2.** A condition carried over from an earlier round or experiment is
  read from its code, citing the line, never from its README's prose
  (squillo L-034).
- **C3.** The generator asserts each condition on what it generated, with
  extremes computed from the output or its exact formula, never from
  nominal parameters, and stops if one fails.
- **C4.** Any procedure that makes the truth (alignment, segmentation)
  runs on one input of every condition first.

*Checks of the checks*

- **C5.** A check's bounds are computed in code from their source's
  definition, never retyped; a bound is a named constant whose own line
  states its source (a definition, a lab result, literature), never a bare
  number in a comparison (squillo L-057).
- **C6.** A tolerance built from a resolution also carries the rounding of
  the arithmetic that makes the values it compares, at their magnitude
  (squillo L-048).
- **C7.** An expected value is computed from the definition on the exact
  input the check reads (a gate's blocks that straddle a silence's edge
  included), never its nominal value (squillo L-054).
- **C8.** A tolerance on two implementations' agreement is built from
  their differences read from both codes (coefficients, framing, how a
  count is rounded), each bounded; where one cannot be bounded the
  agreement is recorded, not asserted, and the rule reads the stricter of
  the two (squillo L-054, E-001 round 3).
- **C9.** A tool's arrays are matched to frames by the index it returns,
  never by position.
- **C10.** Every check is run once on a case it must pass and once on a
  case it must fail, each known independently of the check. **A must-fail
  case differs from the must-pass case in the input the check reads**:
  never the check applied to identical arguments, never a value that
  cannot fail by construction, and never an expectation taken from the
  claim under test (a finding being re-derived is not its own must-fail
  case). A must-fail asserted over runs first asserts that the runs it
  needs exist and none errored. **The must-fail input is chosen from the
  formula the check reads, naming the term it moves and why that term
  decides the outcome** (scaling a term another term dominates cannot
  fail). **Every check of a check runs, and stops the run if it fails,
  before any bar's outcome or hypothesis's result is computed, and no
  assertion message carries one**, so a check revised after a stop is
  revised unseen (squillo L-061, E-002 round 5's revisions 2 and 3).
- **C11.** A pass bar or a selection rule written before a run is a check
  too: it is applied first to the reference condition that must pass it
  (such as clean input on the fitting fold) and to one that must fail it.

*Rules that predict*

- **C12.** A rule that predicts what a change leaves unmoved over a set of
  inputs is written only after each input's value of the condition the
  change acts on is read (from its generator or manifest), and names the
  inputs the change is expected to move (squillo L-058, E-005 fold 4).
- **C13.** A rule that predicts an outcome on every input of a set (every
  state found, every take measured) is written only after the rate at
  which the experiment's own earlier results gave that outcome is read;
  where that rate was below 100 % it names why each of its inputs will not
  be the exception, or it is reported without a bar (squillo L-059, E-005
  fold 5).

*Commit order and the guard*

- **C14.** Rules and bars written before a run are committed before it
  runs, in their own commit, so that "before" can be read from git; a
  fixture generator's or model's expected outcomes are such rules.
- **C15.** A script that holds rules or expected outcomes refuses to run on
  an uncommitted edit of itself, or before it has been committed at all
  (`git ls-files --error-unmatch <script>` and `git diff --quiet HEAD --
  <script>`, since the second passes for a file git has never seen; E-003
  `fixtures.py`, `r3_bridge.py`, `r4_analyze.py`, `committed_first`, and
  E-006 `run.mjs`, `analyze.mjs`), so that running first is not possible
  by accident (squillo L-047, L-049). A new script is written with its
  guard in its first draft, never added on review, and the guard covers
  every module of the experiment that holds a rule, not only the entry
  script (squillo L-051).
- **C16.** **Before the first run** of any script that holds a rule or an
  assert, a fixture generator or a diagnosis written after the results
  included, `python3 tools/checkkeys.py <script>` runs on it alone and its
  guard flag is fixed first (squillo L-055, L-056).

*Before the results commit*

- **C17.** A condition a check records but does not assert is not a
  check: search the code for an assert of every results key that names a
  check (`check`, `must`, `pass`), and assert it, or say in its README row
  "recorded, not asserted" and why (squillo L-046).
- **C18.** **Then run `python3 tools/checkkeys.py <script>
  <results.json>...`** in a command of its own, and read its output
  before the README's check paragraph is written and before the results
  commit; never chain it to the commit (squillo L-059). It flags a script
  with no committed-first guard and a check key neither asserted by name
  nor listed as recorded; each flag is fixed, or read by hand and listed
  in the README with why (it reads names, not data flow).
- **C19.** The README reports the checks' numbers.

(S15's lessons: squillo L-024, L-026, L-028, L-030, L-031, L-032, L-034,
L-036, L-041, L-046, L-047, L-048, L-049, L-051, L-054 to L-059, L-061.)

**Name the reference before comparing** (squillo standing instruction S16).
A check against an outside source names its reference item in advance: the
article's score block, the person's entity, the edition. It never takes the
best match among several, because a different work can match. Caches of
outside reads are keyed by the whole request (squillo L-027). A field
read from an outside page or file is read by the label or form the source
itself gives it, checked on one item of each kind the source has (each
page layout; each version of a file format the run reads, such as MIDI
from each LilyPond generation) before any rule reads it. A file the
source lists but does not serve is an outcome recorded for its item, not
an error retried (squillo L-050; E-004 round 3's `survey`, `head_ok`,
`ly_words`).

**Place every anomaly in the input's own structure** (squillo standing
instruction S17). When a known input passes through a system the lab does
not control (a browser's fake device, a looped source, a codec), the
analysis records where each anomaly falls in the input: its start, a loop
point, a file boundary. One that falls there is attributed to the input
path until a run without that structure clears it. A bracket counts as
falling there when it holds the point: its position in the input's own
time wraps, or it is longer than the loop (squillo L-032). A sign or direction
stated in a result's legend is derived from the measure's definition in the
code and checked by hand on one case (squillo L-029, L-032). An item left
out as an anomaly is first tested against every other cause the
experiment's own rules name (such as a steady tone's period ambiguity),
with the test's numbers in the README, before it is called unattributed
(squillo L-046).

**Time the full run before starting it** (squillo standing instruction
S19). Before a run longer than a few minutes, time a sample of its items
spread over its conditions, **every extreme and every must-fail condition
among them, each run to its end** (a sample item that does not end is a
fault in the harness; squillo L-048), **on the pool itself, at the process count the
run will use**, since a single idle process can be several times faster
than the same work under a full pool; multiply out, and write the estimate
in the README's command block, **and commit that estimate before the full
run starts**, with a revision of the rules or on its own, so that git
shows it came first (squillo L-051). **The rules are committed before the sample runs**: the sample, and the analysis timed on its outputs, are runs, and an analysis that prints the hypotheses' outcomes on the sample before the rules commit is the rules written after seeing data. A harness fault the sample finds is fixed in a revision recorded before the full run (E-003 round 4, `81f216c`; squillo L-049). If the run and its analysis do not fit well
inside the session, cut the design (fewer cells, fewer items per cell)
before starting, never after (squillo L-033). A run longer than a few
minutes saves its results as it goes and resumes from them, and no time
limit around it is shorter than the estimate allows (squillo L-037). A
survey or download from an outside source is a run too: before it,
count its requests and multiply by their spacing (squillo L-039). So is
the analysis of a run: before it runs on everything, time it on the
sample's own outputs at the pool it will use, and write that estimate
beside the run's (squillo L-044).

**Every claim about the code is matched to the code** (squillo standing
instruction S18). Before committing a README's check table, a docstring or
a commit message that says what the code does (a bound read from a line, a
condition asserted, a case run), match each clause to the line of the
diff or the result that makes it true. Remove or make true a clause with
none. A check with no must-fail case says so in its own row (squillo
L-032, L-035). Likewise every number a README's result row, `INDEX.md` or a
squillo spec, ADR, question, finding, review or ledger row takes from a run,
a proposed correction included, is matched to the results
entry that holds it, for the same takes and the same definition (a gross
error is not an octave error; a re-synthesis is not an original); a number
no results file holds is written to one or not stated (squillo L-038,
L-040).

**A result is a number with its conditions.** State what was measured, on what
input, with which tool versions, and the uncertainty. "Works well" is not a
result.

**Needs a human.** Some experiments need a real microphone, a real room or a
real listener. Their README says so in the status line (`needs-human`) and
gives Joakim a protocol short enough to run in 15 minutes. All of them run from
one local page: `python3 session/serve.py`, then open `http://localhost:8010/`.
It records in the browser into each experiment's ignored `data/cache/human/`,
runs the protocol's scripts, takes the ratings and notes, and commits only the
protocol's result files when Joakim presses *Commit*. An experiment that adds
a `needs-human` step adds it to `session/` too.

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
- **squillo's own checks**: `python3 tools/restatements.py <squillo>` flags
  restatements of an ADR's status that disagree with its header (S4) and
  constraint tables that miss a `docs/architecture.md` §2 row or say "none"
  with no reason (S6); `--self-test` runs its must-pass and must-fail cases.
  A lead, not proof (squillo L-049). `python3 tools/checkkeys.py <script>
  <results.json>...` flags a missing committed-first guard and check keys
  neither asserted nor listed as recorded (S15, checklist C16 to C18; squillo L-051).
- **GPU**: an Intel Arc A770M, which stands in for the remote tier and not for
  a singer's device. Read [`COMPUTE.md`](COMPUTE.md) before timing anything on
  it.

## Status

See [`INDEX.md`](INDEX.md).
