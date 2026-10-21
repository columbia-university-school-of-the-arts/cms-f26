---
name: research-repo
description: "Week 7: make the student's fleet repository the home of their research, with their working thesis, an intake folder, sources stored in Git LFS, and the gate that checks each source's note on every push. Brings the clone they already have up to the course starter by merging it, writes the first thesis if there is none, and hands off to Claude Code in the repository. Run it after /cms-lab:init. Safe to run again."
---

# Your research, in your repository

Make the student's fleet repository, `cms-f26-fleet-<login>`, the home of
their research. Once this skill has run, it holds:

- `thesis.md`, their working thesis, which every source answers to;
- `intake/`, where they drop a PDF, an EPUB, a Word file, or a link;
- `sources/<id>/`, one folder per source, holding the original (stored in Git
  LFS), its Markdown, and the student's note;
- `graph/`, the thesis and how each source bears on it, one line of JSON
  each;
- the gate, a GitHub Action that checks each source's note on every push.

All of it comes from the course starter, merged into the clone the student
already has. Most students have commits of their own there, so the usual path
is to find that clone and merge into it. The student may be new to the
terminal. Say what each command does in one sentence before running it.

This skill works inside the student's clone. It may commit there, and every
push is the student's to make. At a merge conflict it undoes the merge and
stops for help. It runs from any folder. Claude Code may put the shell back in
its own folder between commands, so every command below names the clone:
`git -C "<clone>"` for git, and `cd "<clone>" &&` in front of anything else.
`<clone>` stands for the clone's full path, written out from `/` because a
shell leaves `~` unexpanded inside quotes. Every command quotes it, since a
clone in iCloud sits under `~/Library/Mobile Documents/`, a path with a space
in it.

**Commands you cannot run.** Your shell cannot answer a password prompt or a
sign-in. Hand any such command to the student, with the exact line in a code
block: they open a second Terminal window (⌘-N on a Mac; a new Ubuntu window
on Windows), paste it there, and tell you when it finishes or paste back any
error. Never ask the student to type a password into this conversation.

## 1. Check the machine

These are the checks from `init`'s Week 7 rows. They print Git LFS's version,
the setting `git lfs install` writes, monolith's version, and the email git
signs commits with:

```sh
git lfs version
git config --global --get filter.lfs.process
monolith -V
git config --global user.email
```

Run two earlier rows' checks as well: `gh auth status`, which names the
GitHub account this machine is signed in to, for step 2; and
`python3 --version` with `python3 -m venv --help`, which must show Python 3.10
or later with its virtual environments, for step 6.

If any check fails or prints nothing, show the student which one, send them
to `/cms-lab:init`, which installs and sets up everything on that list, and
stop. They run `/cms-lab:research-repo` again once `init` has finished.

## 2. Find the repository

This prints the GitHub username the machine is signed in as, the `<login>` in
every name below:

```sh
gh api user --jq .login
```

The student's repository is
`columbia-university-school-of-the-arts/cms-f26-fleet-<login>`. This asks
GitHub for it by name and prints the name GitHub answers with:

```sh
gh api repos/columbia-university-school-of-the-arts/cms-f26-fleet-<login> --jq .full_name
```

The repository exists only when that prints exactly the name asked for. An
error means GitHub shows this account no such repository, and a different
name means a rename redirect answered, which counts as missing too. Never
test with `gh repo view`, which follows a rename and succeeds for a repository
that does not exist.

If it is missing, show the student the login first. If it is an account they
do not use for the course, hand over `gh auth login` so they can sign in to
the right one, then run this skill again. A private repository also stays
hidden until its invitation is accepted, and this lists the invitations
waiting for them:

```sh
gh api user/repository_invitations --jq '.[].repository.full_name'
```

If theirs is listed, they accept it in the browser at
`https://github.com/columbia-university-school-of-the-arts/cms-f26-fleet-<login>/invitations`,
and you ask GitHub again. Otherwise, tell the student to send BG their GitHub
username through the Courseworks assignment, and stop. BG makes the
repository.

## 3. Find the clone

This looks through the home folder, four levels deep, for a folder with the
repository's name:

```sh
find ~ -maxdepth 4 -type d -name "cms-f26-fleet-<login>" 2>/dev/null
```

On a Mac, the system may ask whether the terminal may open Desktop,
Documents, or Downloads; allowing it lets the search look there. A result
counts as a clone when it holds a `.git` folder (`test -d "<path>/.git"`) and
`git -C "<path>" remote get-url origin` names `cms-f26-fleet-<login>`.

- **One clone:** work there. Its path is `<clone>` from here on.
- **Several:** show each with its last commit
  (`git -C "<path>" log -1 --format='%cr: %s'`) and ask which one the student
  works in.
- **None:** this copies the repository from GitHub into the home folder:

  ```sh
  gh repo clone columbia-university-school-of-the-arts/cms-f26-fleet-<login> ~/cms-f26-fleet-<login>
  ```

  If `~/cms-f26-fleet-<login>` already exists without a `.git` inside, show
  the student what it holds and ask before cloning anywhere.

A clone inside Google Drive, iCloud, or Dropbox is at risk: the sync service
writes into `.git` while git does, which can corrupt the repository, and it
would upload every original in Git LFS twice. The path usually shows it, with
`CloudStorage`, `Google Drive`, `Mobile Documents`, `iCloud`, or `Dropbox` in
it. On a Mac, Desktop and Documents may sync to iCloud as well, so for a clone
under either, ask the student. When the clone is in a synced folder, say so
and recommend recloning to `~/` with the line above. Anything committed there
and never pushed must reach GitHub first: after
`git -C "<clone>" fetch origin`,
`git -C "<clone>" log --oneline origin/main..` lists it, and pushing it is the
student's to do. Then carry on in the new clone, which is `<clone>` from here
on. The old copy can stay until they have checked the new one. If they prefer
to stay where they are, carry on there.

## 4. Save the student's work first

This lists every file that differs from the last commit, one per line:

```sh
git -C "<clone>" status --porcelain
```

It must print nothing before the merge, so that the starter's files never mix
with unsaved work. If it prints anything, show the student
`git -C "<clone>" status`, ask what each change is, and help them commit it:
stage the files they choose by name, with a message in their words. Stage
nothing under `corpus/`, and never use `git add -f`: a file git refuses stays
out. Anything the student would rather keep out of git, they move out of the
folder themselves. Run the check again until it prints nothing.

The merge goes into `main`. This prints the branch the clone is on:

```sh
git -C "<clone>" branch --show-current
```

If it is another branch, ask the student before switching with
`git -C "<clone>" switch main`. If they would rather stay on it, stop, and
tell them to ask for help in the room, with the branch in the message: "My
clone is on branch `<branch>`, and the Week 7 merge goes into `main`." On
`main`, this brings in any commits GitHub has that this copy lacks, so that
their next push goes through:

```sh
git -C "<clone>" pull --ff-only origin main
```

If it reports that the branches have diverged, stop for help in the room.

## 5. Merge the starter

This prints the address of `upstream`, the course starter, if the clone has
one:

```sh
git -C "<clone>" remote get-url upstream
```

If it fails, this adds it:

```sh
git -C "<clone>" remote add upstream https://github.com/columbia-university-school-of-the-arts/cms-f26-fleet-starter.git
```

If it names a repository other than `cms-f26-fleet-starter`, show the student
and ask before pointing it at the starter with
`git -C "<clone>" remote set-url upstream https://github.com/columbia-university-school-of-the-arts/cms-f26-fleet-starter.git`.

This downloads the starter's latest commits and leaves the student's files as
they are:

```sh
git -C "<clone>" fetch upstream
```

If the fetch fails, show the error and stop for help in the room. This joins
the starter's Week 7 scaffold to the student's own history, keeping both,
under git's standard merge message:

```sh
git -C "<clone>" merge --no-edit upstream/main
```

"Already up to date" means an earlier run brought the scaffold in; carry on.

On a conflict, show the student the files git could not combine
(`git -C "<clone>" diff --name-only --diff-filter=U`), then undo the merge,
which puts every file back as it was before this step:

```sh
git -C "<clone>" merge --abort
```

Stop there, and tell the student to show this screen to BG or a TA in the
room. Resolving a conflict means choosing between their work and the
starter's, and they make that choice with help beside them.

## 6. Set up Git LFS and the converter

This sets Git LFS up inside the repository, adding the hooks that send each
original to LFS storage when the student pushes:

```sh
cd "<clone>" && git lfs install
```

This makes `.venv`, the repository's own Python environment (git ignores it),
and installs MarkItDown there. MarkItDown is the converter the hook uses to
turn each source into Markdown.

```sh
cd "<clone>" && python3 -m venv .venv && .venv/bin/pip install -r .claude/hooks/requirements.txt
```

Tell the student it takes a minute or two, and that a quiet terminal
meanwhile is normal. A rerun finds MarkItDown in place and finishes sooner. If
it fails, show the error, note it for the hand-off, and go on to step 7, which
needs no converter; the hook says plainly when `.venv` is missing.

## 7. Write the thesis, if there is none

If `<clone>/thesis.md` exists, show its frontmatter, say the thesis is
already there, and go on to step 8. If it is missing, write it now, in this
run: the gate fails every push until `thesis.md` exists with a version, so
the thesis arrives before the student pushes anything.

Ask for two things, in the student's words, and wait for each: the working
thesis, as it stands tonight (a sentence to a paragraph, and expected to
move), and the question behind it. They may paste both from wherever they
wrote them. Write what they say. You may tidy their sentences; read the
result back and let them change it. The argument stays theirs.

`date +%F` prints today's date as `YYYY-MM-DD`. Write `<clone>/thesis.md`:

```markdown
---
version: 1
date: YYYY-MM-DD
---
<the working thesis, in the student's words>

## The question behind it

<the question, in the student's words>
```

Unless `<clone>/graph/nodes.jsonl` already holds a line with the id
`thesis-v1`, this appends the thesis's node to it as one line, with today's
date in place of `<today>`:

```sh
printf '%s\n' '{"id": "thesis-v1", "type": "thesis", "version": 1, "date": "<today>"}' >> "<clone>/graph/nodes.jsonl"
```

The starter ships that file empty, and `printf '%s\n'` ends the line with a
newline, so the first source's node starts a line of its own.

This records both files in one commit:

```sh
git -C "<clone>" add thesis.md graph/nodes.jsonl
git -C "<clone>" commit -m "Thesis, version 1"
```

This runs the gate on the student's machine and prints what GitHub will say
about their next push; with a thesis and no sources yet, it passes:

```sh
cd "<clone>" && python3 .github/gate.py
```

If it fails, show the student its output and stop for help in the room.

## 8. Turn off "Help improve Claude"

Remind the student to turn off "Help improve Claude", in Claude's Settings,
under Privacy, and ask them to say when it is off. Sources they bring from
the library are licensed to Columbia, and with this setting off, the
conversations that read them stay out of model training.

## 9. Hand off

Tell the student, in two or three sentences, what changed: the scaffold
merged, the converter installed, and the thesis committed (or already there),
with anything that failed. Their commits are on this machine; when they are
ready, `git push` from the clone sends them to GitHub, where the gate runs.

Then work out where this session is running. Use the folder Claude Code was
started in, which the session's environment lists as the primary working
directory; the shell's current folder can drift between commands and is not
the evidence. If that folder is `<clone>`, tell the student they are already
in the repository and need no `cd` and no restart. Otherwise give them the way
into the repository, to run after `/exit` here or in a new Terminal window
(with the clone's full path, in quotes, if it lives elsewhere):

```sh
cd ~/cms-f26-fleet-<login> && claude
```

The first time Claude Code opens there, it asks whether to trust the folder.
Accepting lets the repository's hook run, and the hook files each source that
lands in `intake/` when Claude Code starts. Tell them to start Claude Code
before dropping anything in `intake/`. A file dropped while it runs waits
until they tell Claude about it, so a course reading can be named as one and
go to `corpus/`, which stays on this machine. A file dropped in while Claude
Code is closed is filed when it next starts. It goes in as a course reading
when `corpus/` already holds a file of the same name, extension aside, and
otherwise as an ordinary source, which the student's next commit would carry
into the repository.
