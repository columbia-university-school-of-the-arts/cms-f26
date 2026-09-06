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

The scripts live here, and you download them in your browser. Sign in to
GitHub first: this repository is private to the class, and the invitation you
accepted is what lets you see it.

**On a Mac.** Open [`setup.sh`](setup.sh) and press the **download** button on
the file's page (the arrow icon beside "Raw"). It lands in your Downloads
folder. Then open Terminal (⌘-Space, type `Terminal`, press return) and paste
this one line:

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

- **The browser shows the script as text instead of downloading it.** You
  pressed **Raw**. Go back and press the download icon beside it.
- **GitHub says the page does not exist.** You are not signed in, or you have
  not accepted the invitation to the class organization. Check your email for
  it; the same invitation is what lets you clone your repository later.
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
16 September, which is the night the toolchain installs.

### For instructors

Students download both scripts from this repository in a browser, so what
they run is always the current file and nothing is copied to Canvas. Both
scripts still print their version on every run; ask a stuck student what
version theirs reports, since a download from before a fix is the likeliest
cause.

The session sheets in `sessions/` do get a Canvas copy, pasted by hand for
anyone who cannot yet open this repository, and each carries a version line at
the top for the same reason.

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

`cms-week1` carries `corpus-artifact`, which takes whatever a student asks to
make from a folder of readings and holds it to four rules: every claim cites a
file and a quotation, every relation between texts is stated as a line, every
gap is declared rather than filled, and what the PDF conversion lost is named.
`corpus-map` is the same skill with the shape fixed to a table. Both install
in the first session, in Cowork, and need no repository.

## Your fleet repository

Your own repository is `cms-f26-fleet-<your-github-username>`, created for
you and cloned from the course template. Everything about working in it is
documented inside it: start at its `README.md`, then `docs/map.md`.

## License

CC BY-NC-SA 4.0. Attribution, non-commercial, share alike.
