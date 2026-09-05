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

**On a Mac.** Download **`setup.sh`** from **Files** on the course Canvas site,
then open Terminal (⌘-Space, type `Terminal`, press return) and paste this one
line:

    bash ~/Downloads/setup.sh

**On Windows**, start at [WINDOWS.md](WINDOWS.md) instead — you install WSL
first, then run `setup-wsl.sh` inside it.

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

One thing it deliberately does not do: it does not sign you in to GitHub, since
`gh auth login` opens a browser and is yours to complete. It *does* run
`gh auth setup-git` for you if you are already signed in, which is what lets
`git push` work later without asking for a password every time. If you sign in
afterwards, run the script again — it is safe to re-run and will pick it up.

It also does not install the Claude desktop app; that comes from the
Announcement, before class.

### Windows

Use **WSL**, and see **[WINDOWS.md](WINDOWS.md)** — it walks the whole path.

Short version: on native Windows, `git` and the GitHub CLI both demand
administrator rights that a college loaner laptop may not give you, and no
script can grant. Inside WSL you are the administrator of your own Linux, so
`sudo apt install` just works and the wall disappears. Install WSL once, then
run `setup-wsl.sh` inside it.

The wall stands in exactly one place — installing WSL itself — and whether that
needs administrator rights depends on your Windows version. If `wsl --install`
refuses, tell us before the first session rather than fighting it.

**Not yet tested end to end.** It will be walked on a real machine before
9 September.

### For instructors

This file is the source of truth; the copies on Canvas are what students run.
They drift silently. Both scripts print their version on every run — bump
`SETUP_VERSION` in **both** and re-upload after any change, and ask a stuck
student what version theirs reports.

Four files go to Canvas Files: `setup.sh`, `setup-wsl.sh`, `WINDOWS.md`, and
the session sheet in `sessions/`. The sheet carries a version line at the top
for the same reason the scripts print theirs.

## In the room

Each session's student sheet lives in [`sessions/`](sessions/), one file per
week, with a copy on Canvas for anyone who cannot yet open this repository.
Week 1 is [`sessions/week-01.md`](sessions/week-01.md).

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
