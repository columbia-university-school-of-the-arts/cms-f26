---
name: workflow
description: "From Week 10: turn the student's corrected workflow/workflow.md into a workflow that runs: one stage per step under workflow/stages/, each saying what it reads, makes, runs, and how it is checked, built to the course's stage contract. Run it in Claude Code in the fleet repository. Safe to run again."
---

# From your drawn workflow to one that runs

The student drew their research process by hand in Week 10, Claude read the
photo, and they corrected the result into `workflow/workflow.md`. This skill
turns that file into a pipeline they can run one stage at a time here, or
all at once with `python3 scripts/run_workflow.py`. It works only inside the
student's fleet repository and writes only under `workflow/`,
`.claude/agents/`, and `notes/PATTERNS.md`. Say what each step does in a sentence before doing it.

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

## 3. Build the stages

The workspace is `workflow/`:

- an entry file, `workflow/AGENTS.md`: what the workflow is for in one line; a
  table of the stages, each with its job in five words; how to run a stage
  here and headless; and that a stage's state is its `output/check.md`;
- `workflow/CLAUDE.md`, holding the one line `@AGENTS.md`;
- `workflow/stages/NN_short-name/`, with `CONTEXT.md` and `output/.gitkeep`,
  **one stage per step**, numbered from 01 in the step order.

Each stage's `CONTEXT.md` opens with front matter the course runner reads,
plain `key: value` lines between `---` lines:

```text
---
kind: agent
agent: primary-mapper
allow: Read, Bash(python3 scripts/lantern.py:*)
check: model
timeout: 900
---
```

`kind:` and `check:` come from step 2. An `agent` stage names its `agent:`
and lists in `allow:` only the tools it needs. Never list `Write` or
`Edit`: the runner lets each stage write to its own `output/` and nowhere
else, and refuses an `allow:` line that grants more. A `script` stage has
`command:`. A `script` check has `check_command:`. A `fleet` stage has
`agent:` or `command:` pointing at what already exists, and copies nothing.
A `fleet` stage that names an agent needs an `allow: Bash(...)` line for that
agent's scripts.

`command` and `check_command` run from the repository root; paths under
Inputs are relative to the stage folder.

Use only these keys: `kind`, `agent`, `command`, `allow`, `check`,
`check_command`, `timeout`. The runner refuses any other.

After the front matter, the file follows this template:

```text
# NN_short-name: the job in five words

One job: the single thing this stage does.

## Inputs
- Working (this run): `../NN_previous/output/file.md`
- Reference (every run): `../../../thesis.md`
- Later round (optional): `../NN_later/output/new-queries.md`

Do NOT load: what an eager agent would wrongly pull in.

## Process
1. If a working or reference input is missing or empty, stop and say which.
2. The steps, each one concrete. A step that is code names its command.

## Outputs
- `name.md` in `output/`

## Check
Who or what checks, as one concrete act. A model check's sentence requires the content to be right, not only cited. A check that is not a person writes `output/check.md`, first line `pass` or `fail: <why>`, then two short lists: Observed, and Not established.
```

- A feedback arrow back to an earlier step becomes an output of the later
  stage (for example `output/new-queries.md`) that the earlier stage lists as
  an optional input. The student re-runs from there with
  `python3 scripts/run_workflow.py --redo NN`. On `--redo`, the runner
  copies those files to `workflow/rounds/` before setting outputs aside and
  tells the stage where they are. The earlier stage should also list its own
  previous output as a later-round input (for example
  `../01_find-pages/output/candidates.md`), so a later round can skip what
  round one already found.
- A check that is not a person writes `output/check.md`, first line `pass` or
  `fail: <why>`. A person's check is the student writing that file.
- A model check's sentence decides what passes. Write it to require the
  content to be right (every film named is on the page it is tied to; every
  quote appears in the page text), not only that citations resolve. A check
  that asks only for citations passes a map with misreadings.
- Record state in one place: `output/check.md`. Do not add `status:` lines to
  outputs or any other state vocabulary; the runner reads only `check.md`.
- A check a script can make (quotes found in the page text, cited ids that
  exist) is a `script` check: `check: script` and a `check_command`. A check
  script you write goes in `workflow/_tools/`, is committed with the stages,
  and is named as `python3 workflow/_tools/<name>.py`; it exits non-zero on
  failure.
- Put the judgment early: a stage whose output a person corrects (a list of
  candidates, an outline) comes before the expensive work that depends on it,
  since a correction is cheapest at the first check.

This method is Interpretable Context Methodology (Van Clief and McDermott,
arXiv 2603.16021), which the open-source icm-architect skill implements:
folders carry the sequence, plain files carry the state, and every stage ends
at a check. The course borrows the idea, not the code. Record it in
`notes/PATTERNS.md` with the ledger skill: name the paper and
https://github.com/RinDig/icm-architect, and say what you took.

## 4. The course contract

- Each `agent` stage gets an agent file, `.claude/agents/<name>.md`, with
  `name`, `description`, and `tools` front matter and **no `model:` line**, so
  the student's model setting applies. Its body says what the stage says, in
  the second person, and nothing more.
- No stage file or agent file quotes from `corpus/` or `sources/`. Name
  files; never copy their text. Course readings stay on the student's machine.
- Write `workflow/CLAUDE.md` with the one line `@AGENTS.md`, since Claude Code
  reads `CLAUDE.md` in a folder and not `AGENTS.md`.
- The agent file's `tools:` line names the tools the stage's `allow:` line
  names plus `Read`, `Write`, and `Edit`, since the agent must write its
  `output/`. The stage's `allow:` line names no `Write` or `Edit`; the runner
  grants `output/`.
- Claude Code asks before writing each file in `.claude/agents/`; tell the
  student to expect one prompt per agent and to approve each after reading it.
- Nothing outside `workflow/`, `.claude/agents/`, and `notes/PATTERNS.md`
  changes.

## 5. Check, then commit

Run the check and fix what it reports before going on. It also verifies that
every reference input exists and every working input's folder exists:

    python3 scripts/run_workflow.py check

Then run the walk test: in a fresh reading of `workflow/AGENTS.md` alone, can
you say what the workflow does, what stage comes next, and what state each
stage is in? Then:

    python3 scripts/run_workflow.py status
    git add workflow .claude/agents notes/PATTERNS.md
    git commit -m "My workflow, as stages"

Tell the student how to run a stage here ("run stage 01") and headless
(`python3 scripts/run_workflow.py`), and that a run stops wherever they are
the check. The push is theirs.
