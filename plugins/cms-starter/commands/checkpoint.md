---
description: Restore a week's scaffold floor from the course starter repo
argument-hint: <week number, for example 04>
---

Restore a week's scaffold floor from the course starter.

The student asked for week `$1`. **Normalize it before anything else:** if
it is a single digit (for example `4`), pad it with a leading zero so it
reads `04`. Use that padded form everywhere below, including when you name
the week back to the student, so what they read matches the tag you use.

This recovers the files the scaffold is supposed to have at that point. It
does not contain finished answers.

It replaces **every scaffold file** with that week's version, including any
committed edits of the student's own: `CLAUDE.md`, `README.md`, everything
under `docs/`, `.claude/settings.json`, and `.gitignore`. Not just two files.

It deliberately does **not** touch `notes/`. The ledgers there are the
student's own record, and reverting them would cost work the whole course is
built on. The one exception is a ledger that is missing entirely, which is
restored because an absent ledger helps nobody.

After it runs, the restored files are staged but not yet committed, so
nothing is permanent until the student reviews the change and commits it.

Run these, showing the output of each:

1. `git status --short` and stop if the working tree is dirty. Tell the
   student to commit or stash first, because this overwrites files.
2. `git remote -v` and confirm a remote named `upstream` exists. If it is
   missing, add it:
   `git remote add upstream https://github.com/columbia-university-school-of-the-arts/cms-f26-fleet-starter.git`
3. `git fetch upstream --tags`
4. `git tag -l 'wk*' --sort=-v:refname` to list the tags that actually
   exist, and check whether `wk<padded week>` is among them. If it is not,
   stop here, do not attempt the checkout, and tell the student plainly:
   that week's checkpoint has not been published yet, list the tags that do
   exist so they know what is available, and suggest they ask the
   instructor rather than trying again.
5. Restore that week's files, holding `notes/` back:

       git checkout wk<padded week> -- . ':(exclude)notes/'

   Quote the pathspec exactly as written, or the shell will eat the
   parentheses. Restore from the tag, never from `upstream/main`, because
   main tracks week 1 only.

6. Restore a ledger only if it is missing. For each path the tag carries
   under `notes/`, check whether the student actually has it:

       git ls-tree -r --name-only wk<padded week> -- notes/

   For any of those paths that does not exist in the working tree, and only
   those, run `git checkout wk<padded week> -- <that path>` and tell the
   student you put a missing ledger back. If every path is present, restore
   none of them and say so: their ledger entries were never at risk.
7. `git status --short` to show exactly what changed. Point out that these
   files are staged, not committed, so the student still needs to commit
   them before the restore is permanent (or undo it entirely with
   `git checkout HEAD -- .`, which puts both the staged and working copies
   back the way they were).

Then explain in two sentences what was restored, and remind the student
their own commits are still in `git log`.
