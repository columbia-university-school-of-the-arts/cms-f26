---
name: workflow-map
description: "Use when a student wants to make, start, update, or record a run on a map of their research workflow: from a photo or drawing of their research process, from Claude's reading of that drawing, from a workflow.md, or from a description. Makes one page they keep and grow, with each step, who does it, who checks it, and how to run it in Cowork."
---

# Your workflow, as a map you keep

A workflow map is a page that shows how you do your research: each step, what
goes into it and what comes out, who does it, who checks it, and how to run it
in Cowork. You own it. You change it by asking Claude, in this chat or a later
one, and you start a new one for your next project the same way.

The page is a map of the work. Nothing runs on the page. Steps run in Cowork,
by you or with Claude, in your fleet repository's folder, and you record each
run on the map.

## What to read

Use what the student already has, in this order:

0. **An existing map.** One in this conversation, a section in
   `workflow/map.md` in the attached folder, or JSON the student pastes. When
   the student asks to change the map or record a run, find the existing map
   first; if there is none, ask them to paste its JSON before doing anything
   else. Never build a new map from the drawing when they asked to change one.
1. Claude's corrected reading of their drawing, earlier in this project's
   chat (the Week 10 reading, a Markdown list of steps and arrows).
2. The photo of the drawing, in this chat or the project's files.
3. `workflow/workflow.md`, and `workflow/stages/` if it exists, in the
   attached fleet repository folder.
4. A description the student types now.

Read `thesis.md` in the project's knowledge, or in the attached folder, to
understand abbreviations and terms. Ask the student for a drawing or a
description only when none of these exists.

## The rules

- **Add no step that is not in the drawing or the student's words.** Do not
  improve the workflow while mapping it. Suggestions go in the chat, never on
  the map, until the student accepts them.
- **Mark every guess UNSURE.** A word you cannot read, an arrow you are not
  sure of, a step with no one named to do it or check it: put `UNSURE` in that
  field and say what you think it is in the step's `unsure` list. Settle each
  one with the student before calling the map done.
- **At least one step is the student's alone.** Mark it `mine`. If the
  drawing does not say which, ask.
- **"You" or "it" is the student's answer.** For each step, ask whether Claude
  is a "you" there (someone they consult) or an "it" (a tool they use), and who
  is credited with what the step produces. Write their answers in `you_or_it`
  and `credited`. Never fill these in yourself; leave `UNSURE` until they
  answer.
- **How to run each step in Cowork.** Write `run` as what the student would
  ask Cowork, in their words where possible, or the skill to use. A step done
  by hand says so.

## The map's data

The page keeps the whole workflow in one JSON block,
`<script type="application/json" id="workflow">`. Its fields:

- `title`: a short name for the workflow.
- `question`: the research question, one line, from the thesis.
- `begun`: the date the map was started, `YYYY-MM-DD`.
- `steps`: in order, each with:
  - `n`: the step's number, or a label such as `2a` when the drawing has
    sub-steps.
  - `name`: a few words.
  - `in` and `out`: what goes in, what comes out.
  - `who`: `me`, `Claude`, `a script`, `someone else`, or `UNSURE`.
  - `check`: `by` (`me`, `a script`, `Claude`, `someone else`, or `UNSURE`)
    and `how`, one sentence a person could follow.
  - `run`: how to run it in Cowork.
  - `state`: `not tried`, `tried`, `works`, or `broken`, with `state_date`
    and a one-line `state_note`.
  - `you_or_it`: `you`, `it`, or `UNSURE`; `credited`: who is credited.
  - `mine`: `true` for a step that is the student's alone.
  - `unsure`: a list of what is still uncertain in this step.
- `arrows`: each `from` a step `to` a step, with `loop: true` when it goes
  back to an earlier step. Keep every arrow in the drawing, feedback loops
  included. For an arrow you are not sure of, keep the steps you believe it
  joins, add `"unsure": true`, and explain the doubt in the `unsure` list of
  the step it starts from.
- `changes`: the change log, newest first, each with a `date` and `what`.

Keep every field you do not know exactly as it is. A map made or opened by
the `workflow-interactive` plugin also carries `id`, `kind`, `repo`, `lanes`,
`sources`, `icons`, `git`, and, on steps and arrows, `lane`, `col`, `icon`,
and `label`; change none of them, drop none of them, and treat an arrow whose
`from` starts with `src-` as coming from a data source, not as an UNSURE
arrow. The student keeps working on that map with `workflow-interactive`.

The block must stay valid JSON, or the page shows an error in place of the
map: escape double quotes inside strings as `\"`, leave no trailing commas,
and write `<\/` wherever a string contains `</`, so that a student's
`</script>` cannot end the block.

## Making the page

Start from `references/map-template.html` in this skill. Replace only the
JSON block, keep everything else exactly as it is, and publish the result as
an artifact. Then go through every `UNSURE` with the student,
one step at a time.

## Changing the map

- Update the artifact in place, in the same conversation, and change only the
  JSON block.
- Add a change log line for every change, newest first.
- Never drop a step, an arrow, or a change log line unless the student asks.
- Recording a run sets `state`, `state_date`, and `state_note`.
- If the map is not in this conversation, rebuild it from `workflow/map.md` in
  the attached fleet repository folder, or ask the student to paste the map's
  JSON. Never start a blank map over one that exists.

## Saving a copy in the repository

At the end of a working session, write the JSON block to `workflow/map.md` in
the attached fleet repository folder, fenced as `json`. Keep one section per
map, headed with the map's title: replace that section in place, add a new
section for a new project's map, and rebuild from the section whose title
matches. The student commits and pushes it from the terminal. That copy is how
the map survives a lost chat and moves to a new project.

When no folder is attached, give the student the whole JSON block, fenced, in
the chat at the end of the session, and tell them to keep it: it is what they
paste to continue in a later chat or save to `workflow/map.md` later.

## A new project

For a new research project, start a new map the same way, from a new drawing
or description. Keep the old one; the change log of each is the record of how
the student's practice changed.

## Without the skill

This whole file can be pasted into a project chat as instructions when the
skill is not installed. Without the template, build a single self-contained
HTML page, no external files, readable on a phone and in dark mode, showing
the same fields, with the data in the same JSON block so the next change edits
only the data.
