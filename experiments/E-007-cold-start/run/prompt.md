You are a fresh implementer joining a project. You are given two
repositories and nothing else:

- `/tmp/e007/squillo` — the specification (no code).
- `/tmp/e007/squillo-lab` — the experiment lab (code allowed).

The project's plan says Phase 0 ends when a fresh agent, given these two
repositories, can name what to build first and write the first failing
test without asking a question. You are that agent.

Do this, working from the repositories alone:

1. Name what to build first, and say where in the repositories you read it.
2. Write that first failing test, in
   `/tmp/e007/squillo-lab/experiments/E-007-cold-start/test1/`. The
   specification repository holds no code (its rule 1), so the test goes in
   the lab; it is an experiment, never built on. Use the tools the lab's
   `README.md` names (*Tooling*); they are installed. Do not edit anything in
   `/tmp/e007/squillo`, and write nothing outside
   `/tmp/e007/squillo-lab/experiments/E-007-cold-start/` and `/tmp/e007/report.md`
   (tool caches excepted).
3. Run the test and show that it fails, and why it fails.
4. Log every point you had to guess: anything the repositories did not
   tell you that you needed to decide, however small (a value, a file
   layout, a name, an interface, a tool, what "failing" means). For each,
   say what you needed, where you looked, and what you chose. If you had to
   guess nothing, say so.

Nobody can answer questions; do not stop to ask. Run everything in the
foreground and do not start background jobs.

Write your report to `/tmp/e007/report.md` with exactly these sections:

    ## What to build first
    ## Where I read it
    ## The test (files, the command that runs it)
    ## Its output (the failing run, verbatim, trimmed to the relevant lines)
    ## Guesses (numbered; or "None")

Then end your reply with the report's text.
