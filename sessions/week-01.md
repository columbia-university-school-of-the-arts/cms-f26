# Week 1: build the reader, and catch it being wrong

Coding for Media Studies, Wednesday 9 September. Version 2026.09.05.

Tonight you leave with two things: a terminal you have used, and a folder of
this course's readings that can answer questions about itself. The second
thing will answer confidently and be partly wrong. Finding where is the
exercise.

You do not need to know how to code. You need to be precise, and you need to
check.

You already have one piece of vocabulary from the AI Fluency course:
**Delegation, Description, Discernment, Diligence.** Tonight does all four.
The margin says which is which.

---

## Part 1. The terminal (7:10 to 8:20)

You will run one script that installs four tools. While it runs, we talk about
what a shell is, using its output on your screen as the material. Then you
check it worked, install one thing yourself, sign in twice, and fetch your own
repository.

**On Windows?** Start at `WINDOWS.md` in this repository instead of step 1.
Install WSL, then run `setup-wsl.sh` inside it. Say so in the room; we will
walk it with you.

### 1. Download and run the setup script

*Delegation.* You are about to hand a script control of your machine. Look
first.

Download `setup.sh` from **Files** on Courseworks. Use the Download button,
not the filename. Open Terminal (press ⌘-Space, type `Terminal`, press return)
and paste:

    bash ~/Downloads/setup.sh --dry-run

That prints every command the script would run and runs none of them. Read it.
When you are satisfied, paste:

    bash ~/Downloads/setup.sh

It asks for your Mac password once, when Homebrew installs. Nothing shows while
you type it. That is normal.

Now leave it alone for twenty minutes and watch.

### 2. What you are looking at

The scrolling text is a shell doing four things in order: installing Homebrew
(a package manager), then git, then the GitHub CLI, then Claude Code. Each
line is a command and its result. The script is doing nothing you could not
type yourself, and in step 4 you will.

### 3. Check it worked

When the script says **Done**, close the terminal and open a new one. Then
paste:

    brew --version && git --version && gh --version && claude --version

Four version numbers means you are ready. Twenty-five minutes ago this machine
had none of them.

If you see fewer than four, tell us the exact text on your screen. Do not
retype it from memory.

### 4. Install one thing yourself

    brew install ffmpeg

Same package manager, same kind of command, same scrolling output as before.
The difference is that you typed it. Nothing tonight uses ffmpeg. You will, in
Week 8.

### 5. Sign in twice

    gh auth login

Choose **GitHub.com**, then **HTTPS**, answer **Y** when it offers to
authenticate git, then **Login with a web browser**. Copy the one-time code,
press return, paste it in the browser. When the terminal says you are logged
in, run:

    gh auth setup-git

That lets git push later without asking for a password. Then:

    claude

Choose the **Claude account** option, not the Console one. It opens a browser
to sign in with the Pro account you already bought. When you are back in the
terminal and see a prompt, type `/exit`.

### 6. Fetch your own repository

A repository was made for you before tonight. It is named after your GitHub
username:

    cd ~
    gh repo clone columbia-university-school-of-the-arts/cms-f26-fleet-YOUR-USERNAME
    cd cms-f26-fleet-YOUR-USERNAME
    ls

You now have a folder on your own disk that came from GitHub. That is all for
tonight. You will write into it next week.

If the clone says the repository does not exist, you had not yet posted your
username in the Announcement thread. You will get it in Week 2. Nothing else
tonight depends on it.

---

## Part 2. The reader (8:20 to 8:50), in pairs

One of you is the **Author**, one the **Engineer**. The Author decides what
the question means. The Engineer drives Cowork and keeps asking the hard
question: *what, exactly, do you mean by that?*

### 1. Build the reader

Download the course readings from Courseworks Files into one folder on your
laptop. Name it something you will find again, such as `cms-reader`.

Open the Claude desktop app and start a Cowork session. Create a new project,
point it at that folder, and in the project instructions write two or three
sentences describing what the folder holds: the readings for this course,
one PDF per text, twenty-odd files.

### 2. Describe

*Description.* The Author says, in one plain sentence, what they want to know
about these readings. Tonight the sentence is fixed so the room can compare:

> Make me a table: each reading, its central claim, the week it is assigned,
> and one text it argues with.

### 3. Specify the one rule

Before you send it, pin one thing down together. The Engineer asks: **what
counts as a text's central claim?** Its first sentence? What the author says
they will argue? What they repeat most? The thing you would quote if you had
one line?

Pick one. Write it into the prompt as a second sentence. One rule only. This
is the hard part, and it is the point.

### 4. Build

Send it. Two things happen and both are the lesson.

First, watch what Cowork does before it answers. It will convert your PDFs to
plain text, without asking, because it cannot search a PDF. Ask it what it
just did. Ask what a PDF has that plain text does not.

Second, the table comes back. Every cell is filled. Read it.

### 5. Test it against something you know

*Discernment.* Two checks, both in the room.

Check the **Week** column against the syllabus on Courseworks. The corpus does
not contain the syllabus, so how did it know? Find a row where it is wrong.

Then take the one reading you actually did this week and check its row. Is
that the claim? Is that who it argues with? Have those two authors ever met?

Swap tables with the pair next to you. Where do they disagree?

### Watch for this

*Diligence.* Three limits you will hit, and none of them is a mistake.

- **A converted PDF has no page numbers.** You cannot cite from it. Where did
  they go, and who decided that was fine?
- **The folder does not know what week anything is.** That lives in the
  syllabus, which is not in the folder. A confident Week column is filled in
  from somewhere else.
- **Two readings are missing.** Two assigned texts have no PDF yet, so they
  are not in your folder. Did the table say so, or did it map what it had and
  stay quiet?

Write these down. They are what this course studies.

---

## Homework: ask again, with rules

Cowork gave you a table with every cell filled and no way to tell a read
claim from a guessed one. This week you install a tool that refuses to do
that.

1. In Cowork, open **Customize**, then **Plugins**, then **Add marketplace**.
   Enter `columbia-university-school-of-the-arts/cms-f26`. Install
   **cms-week1**.

2. In your reader project, run `/corpus-map`. Same table, three new rules:
   every claim carries the file and a short quotation it came from; every
   cell it could not fill is listed under **Could not determine**, with the
   reason; and what the conversion lost is named under its own heading.

   Those three rules are Discernment and Diligence written down so a machine
   has to follow them. Compare this table with your first one. Which cells
   moved to the gaps list, and were they the ones you had already caught?

3. On the plugin's page, press **Customize**. Add a fifth column of your own
   choosing, one you would actually use. Run it a third time.

Bring all three tables to Week 2. The session opens by comparing what fifteen
people got.

---

## For Week 2, be ready to say

The one rule you gave the table. The row you proved wrong, and how. One thing
the plugin's version could not determine that the first version had happily
filled in.
