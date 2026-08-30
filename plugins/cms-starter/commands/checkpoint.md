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
does not contain finished answers, but it does overwrite the scaffold files
(`CLAUDE.md` and `README.md`) with the versions from that week's tag,
including any of the student's own committed edits to them. After it runs,
the restored files are staged but not yet committed, so nothing is
permanent until the student reviews the change and commits it themselves.

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
5. `git checkout wk<padded week> -- .` to restore that week's files.
   Restore from the tag, never from `upstream/main`, because main tracks
   week 1 only.
6. `git status --short` to show exactly what changed. Point out that these
   files are staged, not committed, so the student still needs to commit
   them before the restore is permanent (or undo it entirely with
   `git checkout HEAD -- .`, which puts both the staged and working copies
   back the way they were).

Then explain in two sentences what was restored, and remind the student
their own commits are still in `git log`.
