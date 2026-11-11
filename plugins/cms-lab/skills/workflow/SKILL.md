---
name: workflow
description: "Week 11: turn the student's corrected workflow/workflow.md into a workflow that runs: one stage per step under workflow/stages/, each saying what it reads, makes, runs, and how it is checked, built with the vendored icm-architect skill and checked against the course contract. Run it in Claude Code in the fleet repository. Safe to run again."
---

# From your drawn workflow to one that runs

The student drew their research process by hand in Week 10, Claude read the
photo, and they corrected the result into `workflow/workflow.md`. This skill
turns that file into a pipeline they can run one stage at a time here, or
all at once with `python3 scripts/run_workflow.py`. It works only inside the
student's fleet repository and writes only under `workflow/` and
`.claude/agents/`. Say what each step does in a sentence before doing it.

## 1. Read

Read `workflow/workflow.md`, `thesis.md`, and the names (not the contents) of
the files in `.claude/agents/`, `scripts/`, and `sources/`. If
`workflow/workflow.md` is missing, stop: the student makes it first (Week 10).
If `scripts/run_workflow.py` is missing, tell them to run
`git fetch upstream && git merge upstream/main` and stop.

## 2. Ask two things per step, and write the answers down

Go through the steps in order. For each, ask the student, one step at a time:

- **Kind**: `person` (it stays theirs), `script` (a command does it the same
  way every time), `agent` (Claude does it, with only the tools it needs), or
  `fleet` (something already built does it: the intake router, the Week 9
  agent, a course script). Offer your guess from what the step says, and let
  them overrule it.
- **Check**: who or what decides the step's output is good enough to pass
  on: `person`, `script` (a command whose exit status decides), or `model`
  (Claude reads the output against the step's purpose).

Write each answer into `workflow/workflow.md` under its step as two lines,
`Kind: ...` and `Check: ...`. On a second run, skip steps that already have
both lines. Do not build anything until every step has them.

## 3. Build with icm-architect

Use the `icm-architect` skill in Build mode, form **Pipeline**, on the
annotated `workflow/workflow.md`, with these rules:

- The workspace is `workflow/`; stages go in `workflow/stages/`, named
  `NN_short-name`, **one stage per step**, in the step order, numbered from 01.
- Each stage's `CONTEXT.md` follows icm-architect's stage template (Inputs,
  Process, Outputs, Check) and **opens with front matter** the course runner
  reads, plain `key: value` lines between `---` lines:

  ```text
  ---
  kind: agent
  agent: primary-mapper
  allow: Read, Write, Bash(python3 scripts/lantern.py:*)
  check: model
  timeout: 900
  ---
  ```

  `kind:` and `check:` come from step 2. An `agent` stage names its `agent:`
  and lists in `allow:` only the tools it needs. A `script` stage has
  `command:`. A `script` check has `check_command:`. A `fleet` stage has
  `agent:` or `command:` pointing at what already exists, and copies nothing.

  Use only these keys: `kind`, `agent`, `command`, `allow`, `check`,
  `check_command`, `timeout`. The runner refuses any other.
- A feedback arrow back to an earlier step becomes an output of the later
  stage (for example `output/new-queries.md`) that the earlier stage lists as
  an optional input. The student re-runs from there with
  `python3 scripts/run_workflow.py --redo NN`.
- A check that is not a person writes `output/check.md`, first line `pass` or
  `fail: <why>`. A person's check is the student writing that file.
- Record state in one place: `output/check.md`, whose first line is `pass` or
  `fail: <why>`. Do not add `status:` lines to outputs or any other state
  vocabulary; the runner reads only `check.md`.
- icm-architect copies its scripts into `workflow/_tools/` and blank output
  files into `workflow/_templates/`; keep both. A check that one of its
  scripts can make (quotes found in the page text, cited ids that exist) is a
  `script` check: `check: script` and
  `check_command: python3 workflow/_tools/check.py ...`, written to exit
  non-zero on failure.

## 4. The course contract

- Each `agent` stage gets an agent file, `.claude/agents/<name>.md`, with
  `name`, `description`, and `tools` front matter and **no `model:` line**, so
  the student's model setting applies. Its body says what the stage says, in
  the second person, and nothing more.
- No stage file or agent file quotes from `corpus/` or `sources/`. Name
  files; never copy their text. Course readings stay on the student's machine.
- Make sure `workflow/CLAUDE.md` holds the one line `@AGENTS.md`
  (icm-architect usually writes it), since Claude Code reads `CLAUDE.md` in a
  folder and not `AGENTS.md`.
- Nothing outside `workflow/` and `.claude/agents/` changes.

## 5. Check, then commit

Run both, and fix what they report before going on:

    python3 scripts/run_workflow.py check
    python3 -I workflow/_tools/links.py workflow

If icm-architect did not copy `links.py` into `workflow/_tools/`, run it from
this plugin's `skills/icm-architect/scripts/`. Then run icm-architect's walk test: in a fresh reading of
`workflow/AGENTS.md` alone, can you say what the workflow does, what stage
comes next, and what state each stage is in? Then:

    python3 scripts/run_workflow.py status
    git add workflow .claude/agents
    git commit -m "My workflow, as stages"

Tell the student how to run a stage here ("run stage 01") and headless
(`python3 scripts/run_workflow.py`), and that a run stops wherever they are
the check. The push is theirs.
