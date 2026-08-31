---
description: Restore the scaffold floor from the course starter repo
---

Restore the scaffold floor from the course starter.

This recovers the files the scaffold is supposed to have. It does not
contain finished answers.

It replaces **every scaffold file** with the course starter's current
version, including any committed edits of the student's own: `CLAUDE.md`,
`README.md`, everything under `docs/`, `.claude/settings.json`, and
`.gitignore`. Not just two files.

It deliberately does **not** touch `notes/` or `cowork/`. The ledgers in one
and the manual passes in the other are the student's own work, and a
checkpoint that reverted them would destroy the record the final project is
built from.

After it runs, the restored files are staged but not yet committed, so
nothing is permanent until the student reviews the change and commits it.

Run these, showing the output of each:

1. `git status --short` and stop if the working tree is dirty. Tell the
   student to commit or stash first, because this overwrites files.
2. `git remote -v` and confirm a remote named `upstream` exists. If it is
   missing, add it:
   `git remote add upstream https://github.com/columbia-university-school-of-the-arts/cms-f26-fleet-starter.git`
3. `git fetch upstream`. If this fails, say so plainly — do not retry
   blindly — and tell the student to ask the instructor.
4. Restore the current course-starter files, holding `notes/` and `cowork/`
   back:

       git checkout upstream/main -- . ':(exclude)notes/' ':(exclude)cowork/'

   Quote both pathspecs exactly as written, or the shell will glob-expand
   `:(exclude)` and silently do nothing, which would revert the very files
   this command promises to protect.

5. Restore a file only if it is missing. For each path the starter carries
   under `notes/` or `cowork/`, check whether the student actually has it:

       git ls-tree -r --name-only upstream/main -- notes/ cowork/

   For any of those paths that does not exist in the working tree, and only
   those, run `git checkout upstream/main -- <that path>` and tell the
   student you put the missing file back. If every path is present, restore
   none of them and say so: their own work was never at risk.
6. `git status --short` to show exactly what changed. Point out that these
   files are staged, not committed, so the student still needs to commit
   them before the restore is permanent (or undo it entirely with
   `git checkout HEAD -- .`, which puts both the staged and working copies
   back the way they were).

Then explain in two sentences what was restored, and remind the student
their own commits are still in `git log`.
