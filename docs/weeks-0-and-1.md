# Weeks 0 and 1

Everything to do before we meet, and everything that happens when we do.
No coding experience is assumed anywhere in this document.

Week 0 is setup, done at home, and it takes about an hour with most of that
spent watching videos. Week 1 is our first session together, three hours,
where you will turn an idea about a film into a program that runs.

If a Week 0 step fails, stop and email me with what you saw. A stuck step is
expected. It is easy to fix in advance and genuinely hard to fix in a room of
fifteen people.

---

# Week 0: setting up

## 1. Watch three short videos

- The command line:
- Git and GitHub:
- Claude Code:

Watch these first. The words in them are the words the rest of this document
uses.

## 2. Email me two things

**Your GitHub username.** Make a free account at github.com if you do not have
one. I will then send you **two** invitations by email, and you need to accept
both:

- one to your own repository, where your work lives
- one to the CMS-F26 team, which lets you read the course tooling

One click each. If only one arrives, tell me, because the second is what makes
step 7 work.

**Whether you already pay for Claude**, on any plan, or need a key from me.
Both paths work equally well and neither costs you anything beyond what you
already pay. I need the count in advance.

## 3. Install four things, in this order

Each one lets you check the next, so the order matters.

1. **VS Code**, from code.visualstudio.com. It should open to a welcome tab.
2. **Git**, from git-scm.com. Accept the defaults. Then open VS Code, open the
   terminal (View, then Terminal), and type `git --version`.
3. **GitHub CLI**, from cli.github.com. Check with `gh --version`.
4. **Claude Code**, from docs.claude.com/en/docs/claude-code. Check with
   `claude --version`.

> **It worked if:** each of those three commands prints a version number,
> something like `git version 2.43.0`. A number is a pass. An error is not.

## 4. Sign in to GitHub

In the VS Code terminal:

    gh auth login

Choose GitHub.com, then HTTPS, then follow the prompts. A browser window opens
for you to approve access.

> **It worked if:** the terminal prints `Logged in as YOUR-USERNAME`.

## 5. Sign in to Claude Code

In the same terminal, type `claude` and press return, then follow the sign-in
prompts. If you have a paid Claude account, use it. If not, email me for a key.

> **It worked if:** you see a welcome screen and then a prompt you can type
> into. Once you do, type `/exit` to close it. You will start Claude Code again
> in step 7.

## 6. Get your repository

First move somewhere you can find later, then clone. Replace `YOUR-USERNAME`
with your GitHub username in both lines.

    cd Desktop
    git clone https://github.com/columbia-university-school-of-the-arts/cms-f26-fleet-YOUR-USERNAME.git
    cd cms-f26-fleet-YOUR-USERNAME
    git remote add upstream https://github.com/columbia-university-school-of-the-arts/cms-f26-fleet-starter.git

Then open that folder in VS Code: File, then Open Folder, then pick the folder
on your Desktop.

> **It worked if:** typing `ls` lists files including `CLAUDE.md` and
> `README.md`. Your repo is on your Desktop, so you can find it in Finder or
> File Explorer too.

Opening the folder makes a *new* VS Code window with its own fresh terminal.
Any Claude Code session from the old window does not carry over. That is
expected, not a failure.

## 7. Install the course tooling

In the new window, open the terminal, type `claude`, press return, then run
these one at a time:

    /plugin marketplace add columbia-university-school-of-the-arts/cms-f26
    /plugin install cms-starter@cms-f26

> **It worked if:** each command prints its own confirmation, first that the
> marketplace was added, then that `cms-starter` was installed.

More about what you just installed: [About the plugin](https://github.com/columbia-university-school-of-the-arts/cms-f26-fleet-starter/blob/main/docs/the-plugin.md).

## 8. Make your first commit

Still in Claude Code, ask it in your own words:

> Create a file at notes/hello.md that says who I am and one thing I want to
> get out of this course. Then commit it and push.

Watch the file appear in the file tree on the left. That is the whole point of
this step. You asked in English, and a file exists.

> **It worked if:** the push finishes without an error. I will see it, and that
> is how I know you are ready.

---

# Week 1: code and/as natural language

**Bring** your laptop with Week 0 finished, and the reading. We will spend the
first stretch on the question of whether code is a language at all, then move
to the terminal, then build something in pairs.

**The exercise.** Fifty years of *Rocky* (1976). You will take an idea about
the film, in plain English, and turn it into a small program that runs on the
film's subtitles. You do not need to know how to code. You need to be precise,
and precision is the hard part.

## Your two roles

| Role | Does |
|---|---|
| **Author** | Has the idea and decides what it should mean |
| **Engineer** | Drives Claude Code and keeps asking the hard question: what, exactly, do you mean by that? |

You will switch after the first round, so both of you do both jobs.

## The loop

### 1. Get the files into your repo

Download `rocky_1976.srt` and `rocky_3.srt` from Courseworks, then put them in
a new folder inside your repo:

    runs/week01-rocky/

Your repo already expects work to live under `runs/`, one folder per piece of
work. This is the first of many.

### 2. Describe

The Author names, in one plain sentence, a tool you wish existed for studying
this script. For example, "a tool that finds the film's most emotional
stretch."

### 3. Specify

Together, pin that idea to something a machine can follow. Fill in three
blanks:

    Input:    the subtitle file (.srt), which gives the
              spoken lines and their timestamps.

    The rule: my tool decides ____________
              by looking only at ____________.

    Output:   the tool returns ____________.

**One rule only.** This is the hardest step and it is the point of the whole
exercise.

### 4. Build

Ask Claude Code to write a program that follows your spec and run it on
`rocky_1976.srt`. Watch the file tree on the left.

> **The move that matters.** If Claude answers your question in prose instead
> of writing a program, say: **"write it as a file and run it."** Telling those
> two apart, a model that replied versus a model that made something you can
> re-run, is the single most useful thing you will learn today.

### 5. Test on a film you did not plan for

Run the same program, unchanged, on `rocky_3.srt`. Does the result still make
sense? What broke?

### 6. Commit, then switch roles

Ask Claude Code to commit your work with a short note saying what the tool
does. Then swap Author and Engineer and run the loop again.

## If you are stuck for an idea

Find the quietest stretches of dialogue across the runtime, which in *Rocky*
tend to be the training montages and the final fight. Count how often a word
like "champ" or "contender" appears. Measure who talks the most. Sketch a rough
mood curve from start to finish. Pick one and make it precise.

## Watch for this

Subtitles carry the words and their timing. They do not tell you who is
speaking or what is on screen. If your tool needs that, you have found a real
limit of the data rather than a mistake you made. Write it down. That is
exactly the kind of thing this course studies.

## Be ready to say, at the share-out

- Your one-sentence idea.
- The single rule you gave the tool.
- Where it broke or surprised you, and how you would check whether it is right.

---

## If something breaks in Week 0

Email me with the step number and exactly what you saw, including the error
text. Copy the error rather than retyping it from memory, because the exact
wording is usually the whole answer.

Optional office hour before our first session:

## Where to go next

- [Where everything is](https://github.com/columbia-university-school-of-the-arts/cms-f26-fleet-starter/blob/main/docs/map.md)
- [Words this course uses](https://github.com/columbia-university-school-of-the-arts/cms-f26-fleet-starter/blob/main/docs/glossary.md)
- [Getting back to a working state](https://github.com/columbia-university-school-of-the-arts/cms-f26-fleet-starter/blob/main/docs/recovering.md)
