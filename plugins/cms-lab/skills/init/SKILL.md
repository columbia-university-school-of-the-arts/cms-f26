---
name: init
description: "Ready the student's machine for the CMS course lab: check and install every tool the course has introduced so far (git and GitHub sign-in, Python, FFmpeg, yt-dlp's JavaScript runtime, and each later week's additions), create ~/cms-lab, and record the result. Run it first, and again whenever the course adds a tool; it catches up a student who missed any number of weeks. Safe to run repeatedly."
---

# Get the lab ready

Make this machine ready for every `cms-lab` project the course has reached,
so that when the student starts one, nothing slow or system-wide is left to
install. The student may be here on time, weeks late, or catching up after
missing class; the job is the same: bring the machine up to date with the
list. They may be new to the terminal. Say what each command does in one
sentence before running it.

This skill touches only the machine's tools and the `~/cms-lab` folder. It
creates no project, downloads no video, and makes no repository, fork, commit,
or push. It runs from any folder.

## 1. Read the list, then look

`references/tools.md` beside this skill is the whole list, one row per tool,
with the week it arrived, the check that proves it works, and how to install
it on macOS and inside WSL. Work through every row, top to bottom. Do not
skip earlier weeks: a student who missed them needs them most.

Work out the platform first (`uname -s`; WSL reports Linux, and
`/proc/version` mentions Microsoft). Run each row's check and show the student
a short table: tool, week, present or missing, version. If
`~/cms-lab/lab-setup.md` exists, compare against it and say what is new since
their last run.

## 2. Install what is missing

Install only rows whose check fails, in table order, using the platform's
column. Group Homebrew installs into one `brew install` line. Re-run each
row's check afterwards; a row counts as done only when its check succeeds.

If a slow install is running (FFmpeg through Homebrew can take minutes), tell
the student it is slow, not stuck, and point them to the week's by-hand work
meanwhile.

**Commands you cannot run.** Your shell cannot answer a password prompt or
any other interactive question. Hand such a command to the student: `sudo …`
always, any `brew` step that asks for the Mac password, and interactive
sign-ins such as `gh auth login`. Hand over any command that fails for want
of permission, too. Say why, give the exact line in a code block, and tell
them: open a second Terminal window (⌘-N on a Mac; a new Ubuntu window on
Windows), paste it there, type your password if asked (nothing shows while
you type), and tell me when it finishes or paste back any error. Wait, then
re-run the check. Never ask the student to type a password into this
conversation.

If an install fails, show the actual error. Do not work around it with a
different package manager, an unofficial download, or `sudo` you run
yourself. Show any downloaded installer script to the student before running
it. Record the failure and tell the student to ask in the room or on the
course site; carry on with the rows that do not depend on it.

## 3. Make the lab folder and record the machine

```sh
mkdir -p ~/cms-lab
```

Write `~/cms-lab/lab-setup.md`, replacing any earlier copy: the date, the
`cms-lab` plugin version, the platform, one line per row (week, tool, version
or failure), which JavaScript runtime yt-dlp should use, and what this run
installed. Projects read this file to know the machine is ready.

## 4. Hand off

Tell the student, in two or three sentences, whether the machine is ready and
what changed. Then give them the way into every lab project:

```sh
cd ~/cms-lab && claude
```

and the project for the current week. If the week's by-hand work comes first
(tonight, marking cuts in the clip), tell them to finish that before starting
the project.
