# Coding for Media Studies (CMS 2026)

Columbia University School of the Arts. Behrang Garakani and Rob King.

This is the course hub: what to do before the first session, and the tooling
you install into Claude Code. Your own work lives in your own repository,
which is documented from the inside.

## Start here

Setup instructions live on the course Canvas site, not here. That page is what
to do before the first session; this repository is the tooling you install
once you are in the room.

## Installing the toolchain

Download **`setup.sh`** from **Files** on the course Canvas site, then open
Terminal (⌘-Space, type `Terminal`, press return) and paste this one line:

    bash ~/Downloads/setup.sh

That is the whole thing. No unzipping, no `chmod`, no double-clicking.

It installs Homebrew, git, the GitHub CLI, and Claude Code, in that order, and
it is safe to run more than once — anything already present is reported and
left alone.

**macOS only for now.** Windows is being worked out; see below.

### Read it before you run it

    bash ~/Downloads/setup.sh --dry-run    # print every command, run none of them
    bash ~/Downloads/setup.sh --check      # report what you have, change nothing

Not a formality. This course is partly about what you agree to when you hand a
tool control, and an install script is the first thing anyone will ask you to
run unread. `--dry-run` makes no network calls and changes nothing, so looking
first costs you nothing.

The script asks for your password once, when Homebrew installs. That is
Homebrew creating directories it does not yet own.

### If something looks wrong

- **The browser shows the script as text instead of downloading it.** Use the
  **Download** button in Canvas Files rather than clicking the filename.
- **`bash: ~/Downloads/setup.sh: No such file or directory`.** Your browser
  saved it somewhere else, or renamed it (`setup-1.sh` if you downloaded twice).
  Type `bash ` — with the trailing space — then drag the file from Finder into
  the Terminal window, which pastes its exact path.
- **Do not double-click it.** macOS blocks scripts downloaded from a browser
  when they are launched from Finder, and it does so silently enough to be
  confusing. Running it from Terminal is unaffected.

Two things it deliberately does not do: it does not sign you in to GitHub
(`gh auth login` opens a browser and is yours to complete), and it does not
install the Claude desktop app — that comes from the Announcement, before class.

### Windows

Not yet supported. The blocker is not the script: `git` and the GitHub CLI both
require administrator rights on Windows, which no script can grant. A WSL path
is the likely answer and is not settled. Until it is, Windows students install
by hand in Week 2, with an instructor present.

### For instructors

This file is the source of truth; the copy on Canvas is what students run. They
drift silently. `setup.sh` prints its version on every run — bump
`SETUP_VERSION` and re-upload to Canvas after any change, and ask a stuck
student what version theirs reports.

## The course plugin

In Claude Code, or in Cowork under **Customize → Plugins → Add marketplace**:

    /plugin marketplace add columbia-university-school-of-the-arts/cms-f26
    /plugin install cms-starter@cms-f26

`cms-starter` carries two things: the `ledger` skill, which records what
your fleet borrows and from where, and `/checkpoint`, which restores a
week's scaffold when your repository gets away from you.

`cms-week1` carries one skill, `corpus-map`, which turns a folder of readings
into a table whose every claim is sourced and whose gaps are declared rather
than filled in. It is installed in the first session, in Cowork, and needs no
repository.

## Your fleet repository

Your own repository is `cms-f26-fleet-<your-github-username>`, created for
you and cloned from the course template. Everything about working in it is
documented inside it: start at its `README.md`, then `docs/map.md`.

## License

CC BY-NC-SA 4.0. Attribution, non-commercial, share alike.
