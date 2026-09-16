<!--
Ported 2026-09-12.
Concept half from docs/rk-lesson-outlines.md, Week 2, which reads RK's outline
at Drive modifiedTime 2026-08-04T20:20Z; the deck "Week 2 Slides" at
2026-09-12T16:00Z confirms the Brunton passage and the search-against-prompt
table. Practice half from decision 5 of
docs/superpowers/specs/2026-09-06-cms2026-artifact-ladder-design.md, with the
toolchain coming from GitHub in a browser per the locked decision of
2026-09-06 rather than the Canvas Files path that decision 5 still names.
The prompt demonstration is BG's: RK's outline asks for it by name.
-->

# Week 2: the terminal, and your artifact in a repository

Coding for Media Studies, Wednesday 16 September. Version 2026.09.12.

Tonight the file you made last week gets a second life. First you widen it in
Cowork and watch what gets invented. Then you install four tools from one
script, sign in twice, fetch a repository that was made for you, put your
artifact in it, and make your first commit. You leave with your own work under
version control and a machine that can run Claude Code.

You did the GitHub Skills course, so you have already made a commit once, in a
browser. Tonight is the same thing from a terminal.

**Bring** your artifact, and every version of it you made.

---

## The concept hour (6:00 to 7:00)

Two readings this week. Noble's first chapter is the concept reading. Colombo
and colleagues on prompt design is the practice one. The hour holds two things
side by side, and the whole term's first thread runs between them.

It opens with a challenge. A meme goes on the screen and you find its origin
with a Google search, in the fewest words possible, with no reverse-image
search. Then you say why you picked those words.

**Search retrieves. Prompting generates.** That is the distinction the hour is
built on.

- What happens when you press return: a **spider** crawls pages, an **indexer**
  builds a searchable store, and a **query handler** interprets what you typed.
  Early search weighted the words on a page. Google's move was to count links
  as well, which is where Noble's politics enter: relevance is a ranking, and
  a ranking is a decision about what matters.
- Every page has two sides, the HTML a machine reads and the page you see.
- **Regular expressions** are patterns for matching text, and the same
  mechanism that finds a word for you is what lets a state censor it.
- Words carry meaning. **Strings** do not. A computer matches and slices
  sequences of characters without knowing what they say. Studying text in
  digital culture needs both kinds of vision at once.

Then the hour turns to prompting, with a second challenge: make an image a
rival group can identify as a film genre, without naming the genre, a title, a
character, an actor, or a filmmaker. Shortest prompt wins.

A search matches strings to retrieve something that exists. A prompt sets a
probability distribution and generates something that does not. The line is not
clean, since search engines now generate and generative systems now retrieve.
Against the commercial craft of **prompt engineering**, which treats a good
prompt as one that gets you what you wanted, Colombo and colleagues propose
**prompt design**: a prompt built as a research instrument, to disclose how the
system understands the world. That is Noble's "search as research", moved to
images.

---

## Compare (7:10 to 7:20)

Fifteen artifacts go on the projector. Say three things about yours: what you
chose to make and the one rule you gave it, one claim you could check, and one
you could not.

The last is the important one. You have been assigned four of the two dozen
texts in that folder, so most of what your artifact asserts about the rest is
beyond your reach to verify. Finding exactly where that line falls, between
what you know and what you are taking on trust, is tonight's real subject.
This is *Discernment* in public, and the honest answer is usually "I cannot
tell yet.

---

## Cowork: widen it (7:20 to 7:45)

First, Behrang demonstrates how a system rewrites your prompt before it makes
an image. Watch for what arrives in the picture that nobody asked for.

Then, in your reader project, ask Cowork to find three sources outside the
folder that bear on your artifact, and to add each with a citation: author,
title, year, and where it found it. These are outside the folder, so the
plugin's rules cannot check them. You can. Search the title. Search the
author. Expect one of them to be invented. Write down which, and what the
citation looked like before you checked.

Keep the artifact as one Markdown file. You will need it at 8:30.

---

## The terminal (7:45 to 8:10)

The files for tonight live in this repository, and you download them in your
browser. Sign in to GitHub first; the repository is private to the class, and
the invitation you accepted is what lets you see it.

**On Windows?** Open `WINDOWS.md` at the top of this repository and start
there instead of running `setup.sh`. Install WSL, then run `setup-wsl.sh`
inside it. Say so in the room; we will walk it with you.

*Delegation.* You are about to hand a script control of your machine. Look
first.

Open `setup.sh` at the top of this repository. On the file's page, press the
**download** button (the arrow icon beside "Raw"). It lands in your Downloads
folder. Then open Terminal (press ⌘-Space, type `Terminal`, press return) and
paste:

    bash ~/Downloads/setup.sh --dry-run

That prints every command the script would run and runs none of them. Read it.
When you are satisfied, paste:

    bash ~/Downloads/setup.sh

It asks for your Mac password once, when Homebrew installs. Nothing shows while
you type it, which is normal. Now leave it alone and watch.

The scrolling text is a shell doing four things in order: installing Homebrew
(a package manager), then git, then the GitHub CLI, then Claude Code. Each
line is a command and its result.

When the script says **Done**, close the terminal and open a new one. Paste:

    brew --version && git --version && gh --version && claude --version

Four version numbers means you are ready. If you see fewer than four, tell us
the exact text on your screen rather than retyping it from memory.

---

## Sign in, and fetch your repository (8:10 to 8:30)

    gh auth login

Choose **GitHub.com**, then **HTTPS**, answer **Y** when it offers to
authenticate git, then **Login with a web browser**. Copy the one-time code,
press return, paste it in the browser. When the terminal says you are logged
in, run:

    gh auth setup-git

That lets git push to GitHub using the sign-in you just did, so it never asks
you for a password GitHub would not accept anyway. Then:

    claude

Choose the **Claude account** option and skip the Console one. It opens a
browser to sign in with the Pro account you already bought. When you are back
in the terminal and see a prompt, type `/exit`.

A repository was made for you before term. It is named after your GitHub
username:

    cd ~
    gh repo clone columbia-university-school-of-the-arts/cms-f26-fleet-YOUR-USERNAME
    cd cms-f26-fleet-YOUR-USERNAME
    ls

Replace `YOUR-USERNAME`, in both lines, with your GitHub username, the one you
posted in the Announcement thread.

You now have a folder on your own disk that came from GitHub. Last week you
made a repository by clicking. This is one, on your machine.

If the clone says the repository does not exist, you had not yet posted your
username in the Announcement thread. Tell us; it takes two minutes to make.

---

## Claude Code: your first commit (8:30 to 9:00)

Copy your artifact into the repository folder. Finder works. Then, in the
terminal, inside the repository:

    claude

You are now talking to Claude Code, which is Claude with a terminal and your
folder. Ask it, in your own words, to do these four things in order, and read
what comes back each time.

1. **Tell me what git status says about this folder, and what each line
   means.** It will say your artifact is untracked. That is git noticing a
   file it has not been told to keep.
2. **Check every citation in my artifact against my reader folder, and list
   any it cannot find.** Tell it where the folder is. If you named it
   `cms-reader` and put it in your home folder last week, that is
   `~/cms-reader`. This is the Week 1 check, done mechanically: *Discernment*
   as a command.
3. **Commit the artifact with a message that says what it is.** Watch it run
   `git add` and `git commit`. Ask it what each did. Then ask it to push, and
   watch `git push` send the commit to GitHub. Open your repository in the
   browser. Your file is there, with your name on it.
4. **Add the course starter as `upstream`, then install `cms-starter`.** Ask
   it to add `https://github.com/columbia-university-school-of-the-arts/cms-f26-fleet-starter`
   as a remote named `upstream`. Then run:

        /plugin marketplace add columbia-university-school-of-the-arts/cms-f26
        /plugin install cms-starter@cms-f26

   If the first line says the marketplace is already added, go straight to
   the second. Finally, ask it to add one row to `notes/INTEGRATIONS.md` recording that
   the conversion that made your artifact possible: Cowork turned those PDFs
   into plain text without being asked, and that converter is the first piece
   of someone else's work inside your project. Record what it was, if you can
   get it to tell you, and what the conversion cost you, starting with the page
   numbers you can no longer cite. That is *Diligence* as a ledger.

Type `/exit` when done.

---

## Homework

1. Run `/checkpoint` once, in Claude Code, inside your repository. It restores
   the course scaffold and leaves your own files alone. Better to meet it now
   than the week something breaks.
2. Add tonight's three outside sources to the artifact in the repository,
   with citations, and commit. Bring the diff.

---

## For Week 3, be ready to say

Which of the three outside sources was invented, and how you knew. What
`git status` said before and after your commit. One citation Claude Code
could not find in the folder, and what you did about it.
