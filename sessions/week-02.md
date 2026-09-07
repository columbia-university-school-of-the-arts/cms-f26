# Week 2: the terminal, and your artifact in a repository

Coding for Media Studies, Wednesday 16 September. Version 2026.09.06.

Tonight the file you made last week gets a second life. First you widen it in
Cowork and watch what gets invented. Then you install four tools from one
script, sign in twice, fetch a repository that was made for you, put your
artifact in it, and make your first commit. You leave with your own work under
version control and a machine that can run Claude Code.

You did the GitHub Skills course, so you have already made a commit once, in a
browser. Tonight is the same thing from a terminal.

---

## Compare (7:10 to 7:20)

Fifteen artifacts on the projector. The places people proved them wrong, and
what `/corpus-artifact` refused to fill in. The different "one rules" the
room gave the same sentence. *Discernment*, in public.

---

## Cowork: widen it (7:20 to 7:45)

First, Rob shows what a system does to your prompt before it acts on it.
Then, in your reader project, ask Cowork to find three sources outside the folder
that bear on your artifact, and to add each with a citation: author, title,
year, and where it found it. These are outside the folder, so the plugin's
rules cannot check them. You can. Search the title. Search the author.
One of them may not be real.
Write down which, and what the citation looked like before you checked.

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
you type it. That is normal. Now leave it alone and watch.

The scrolling text is a shell doing four things in order: installing Homebrew
(a package manager), then git, then the GitHub CLI, then Claude Code. Each
line is a command and its result.

When the script says **Done**, close the terminal and open a new one. Paste:

    brew --version && git --version && gh --version && claude --version

Four version numbers means you are ready. If you see fewer than four, tell us
the exact text on your screen. Do not retype it from memory.

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

Choose the **Claude account** option, not the Console one. It opens a browser
to sign in with the Pro account you already bought. When you are back in the
terminal and see a prompt, type `/exit`.

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
   `~/cms-reader`. This is the Week 1 check, done mechanically. *Discernment*
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
   `cms-week1` was used to make the artifact, with today's date. *Diligence*
   as a ledger.

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
