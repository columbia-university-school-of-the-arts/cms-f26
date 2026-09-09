# Week 1: make something from the readings, and catch it being wrong

Coding for Media Studies, Wednesday 9 September. Version 2026.09.06.

Tonight you leave with one thing you made from this course's readings, in a
folder on your own laptop, that answers questions about itself. It will answer
confidently and be partly wrong. Finding where is the exercise.

You do not need to know how to code. You need to be precise, and you need to
check. There is no terminal tonight. That is next week.

You already have one piece of vocabulary from the AI Fluency course:
**Delegation, Description, Discernment, Diligence.** Tonight does all four.
The margin says which is which.

---

## The overview (7:10 to 7:35)

Four things to hold onto from it, in one line each.

- A model predicts what comes next. It does not look anything up unless a tool
  lets it, and it does not know what it does not know.
- Cowork is Claude working on files and folders you choose. A **project** is a
  folder plus your instructions about it.
- An **agent** is a model that can act: read a file, run a converter, write a
  result. You are about to hand one your reading list. That is Delegation.
- The thing you build is the thing you study. Everything this term is both.

---

## Build the reader (7:35 to 7:50)

Download the course readings from Courseworks Files into one folder on your
laptop. Name it something you will find again, such as `cms-reader`.

Open the Claude desktop app and start a Cowork session. Create a new project,
point it at that folder, and in the project instructions write two or three
sentences describing what the folder holds: the readings for this course,
one PDF per text, twenty-odd files.

Find a partner. One of you is the **Author**, one the **Engineer**. The
Author decides what the thing means. The Engineer drives Cowork and keeps
asking the hard question: *what, exactly, do you mean by that?*

---

## Choose the artifact (7:50 to 8:00)

Decide what you will make from the folder. Anything, inside this shape:

1. **Every claim cites a file** in the folder and a few words you could
   search for.
2. **It relates at least two texts** and names the relation: argues with,
   extends, cites, contradicts, answers.
3. **It is one Markdown file**, a plain-text file whose name ends in `.md`.
   Next week it goes into a repository.

Things that qualify: a map of every reading; a genealogy of one idea across
the term; a timeline of the arguments; a glossary with cross-references; a
debate staged between three authors. "A summary of each reading" does not,
because it relates nothing.

Cannot decide? Make the map: each reading, its central claim, the week it is
assigned, one text it argues with.

---

## Describe, specify, build (8:00 to 8:30)

**Describe.** *Description.* The Author says, in one plain sentence, what the
artifact is. Write it down before anything else.

**Specify the one rule.** The Engineer asks: **what counts as a text's central
claim?** Its first sentence? What the author says they will argue? What they
repeat most? The line you would quote if you had one? Pick one. Write it into
the prompt as a second sentence. One rule only. This is the hard part, and it
is the point.

**Build.** Send it. Two things happen and both are the lesson.

First, watch what Cowork does before it answers. It will convert your PDFs to
plain text, without asking, because it cannot search a PDF. Ask it what it
just did. Ask what a PDF has that plain text does not.

Second, the artifact comes back. Every gap is filled. Read it.

Then ask Cowork to save it into your reader folder as a Markdown file, and
check in Finder, or File Explorer on Windows, that it is there before you
leave. Next week you copy that
file into a repository.

---

## Falsify (8:30 to 8:50)

*Discernment.* Two checks, both in the room.

If your artifact says what week anything is assigned, check that against the
syllabus on Courseworks. The folder does not contain the syllabus, so how did
it know? Find a place where it is wrong.

Then take the one reading you actually did this week and find it in your
artifact. Is that the claim? Is that who it argues with? Have those two authors
ever met?

Swap with the pair next to you. Where do the two artifacts disagree about the
same text?

**Then install the plugin, and ask again.** In Cowork, open **Customize**,
then **Plugins**, then **Add marketplace**. Enter
`columbia-university-school-of-the-arts/cms-f26`. Install **cms-week1**. In
your reader project, run `/corpus-artifact` and describe the same artifact.

Four new rules apply: every claim carries a file and a quotation; every
relation between texts is written as a line you can count; everything it
could not determine is listed under its own heading, with the reason; and what
the conversion lost is named. Compare with your first version. Which claims
moved to the gaps list, and were they the ones you had already caught?

### Watch for this

*Diligence.* Three limits you will hit, and none of them is a mistake.

- **A converted PDF has no page numbers.** You cannot cite from it. Where did
  they go, and who decided that was fine?
- **The folder does not know what week anything is.** That lives in the
  syllabus, which is not in the folder. A confident week is filled in from
  somewhere else.
- **Two readings are missing.** If your artifact covers the whole reader: two
  assigned texts have no PDF yet, so they are not in your folder. Did the
  artifact say so, or did it work with what it had and stay quiet?

Write these down. They are what this course studies.

---

## Homework, in this order

1. **GitHub Skills, "Introduction to GitHub."** In your browser, about an
   hour, nothing to install. You will make a repository, a branch, a commit,
   and a pull request by clicking. Next week you do the same thing from a
   terminal, and the words will already mean something.
   `https://github.com/skills/introduction-to-github`
2. **Run the artifact a second time** with `/corpus-artifact`, at home, and
   compare it with the version from the room and with your first one.
3. **Press Customize** on the plugin's page in Cowork. Add one rule of your
   own, one you would actually want. Run it a third time.

If the marketplace would not install for you in the room, tell us. Do item 1,
and do items 2 and 3 next week.

Bring every version to Week 2. The session opens by comparing what fifteen
people made.

---

## For Week 2, be ready to say

What you chose to make, in one sentence. The one rule you gave it. The place
you proved it wrong, and how. One thing the plugin's version could not
determine that the first version had happily filled in.
