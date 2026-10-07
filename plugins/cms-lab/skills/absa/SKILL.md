---
name: absa
description: "Week 5 workshop: read five critic reviews of a film the student chooses with aspect-based sentiment analysis. The student writes the categories and annotates one review by hand first; then Claude annotates all five, every opinion quoted verbatim and checked by absa.py, and the result becomes a chart to present. Works in ~/cms-lab/absa, not in a repository."
---

# A review is more than its verdict

Help the student turn five film reviews into opinion tuples (what is judged,
in which category, in which exact words, with which polarity) and then into a
chart they can defend. The method is the instructor's *Parasite* project
scaled down to forty minutes. Students have Claude Code but may be new to it:
say what each command does in one sentence before running it.

The rule underneath everything: **no label without a quotation.** A model's
explanation of its own judgment cannot be checked; a quoted span and a
sentence number can, by `absa.py` and by the student.

## Where the work lives

`~/cms-lab/absa/`, a plain local folder. Not the fleet repository: no clone,
fork, commit or push. If Claude Code is not running inside `~/cms-lab`, stop
and give the student this line, then have them rerun `/cms-lab:absa`:

```sh
mkdir -p ~/cms-lab && cd ~/cms-lab && claude
```

The project needs only Python 3.8 or later and its standard library. Check
`python3 --version`. If `~/cms-lab/lab-setup.md` is missing, mention
`/cms-lab:init` for later, but carry on if Python answers.

Copy `assets/lab/` beside this skill to `~/cms-lab/absa/` only if that folder
does not exist. On later runs, read `experiment.md` and continue the student's
work; never overwrite their codebook, annotations or notes. The installed
plugin is a template, not the place to save their changes.

## Step 0: five reviews, as text

Ask which film the group chose and why: a film critics argued about teaches
more than a consensus favourite. They need **five full critic reviews**, not
the one-line Rotten Tomatoes snippets. Rotten Tomatoes links to each review;
the student opens it in their own browser.

Getting the text is the student's job, by copy and paste: they select the
article text in the browser and copy it, then type, in Claude Code,

```sh
! pbpaste > reviews/r1.txt                          # macOS
! powershell.exe Get-Clipboard > reviews/r1.txt     # Windows, inside WSL
```

(the `!` runs a shell command directly). Repeat for `r2` to `r5`. Do not
fetch pages yourself to get around a paywall, a login or a bot block, and
never disguise a script as a browser. A review that will not open is replaced
by another review. If the student would rather fetch openly reachable pages
with a script, see `references/scaling-up.md`, but in class, pasting is
faster. Never write review text from memory or reconstruct a missing one.

Run `python3 absa.py split`. It numbers each review's sentences into
`work/`, creates `reviews/reviews.csv`, and warns about pastes that look like
snippets, paywalls, cookie banners, repeated text or the wrong film. Read the
warnings with the student and fix bad pastes before going on: a bad paste
becomes bad data. Have them fill in `reviews/reviews.csv` (critic,
publication, URL, the Rotten Tomatoes verdict, the critic's score, date).

Do not print whole review texts into the conversation; the files are the
student's copies and stay on their machine.

## Phase 1: categories before the menu

Before any annotation, the group writes its own codebook. Ask them to read
the shortest review and list what the critic actually judges. Then, in their
own words:

> We sort opinions into ___ categories: ___ (one line each). An opinion is
> very positive or very negative only when ___. We skip ___.

Raise what they must decide, without deciding it: is "the film as a whole" a
category, and how will they stop it swallowing everything? Is plot summary an
opinion? Does a comparison with another film count? Does "too" (as in "too
long") make an opinion very negative? Keep it to four to eight categories.

Do **not** suggest category names, show `references/menu.md`, or mention the
instructor's *Parasite* categories at this stage. Their categories may be odd;
that is the point.

Write `codebook.json` from their words: `film`, `guard_terms` (the title and
director's surname, used by `split` to spot wrong pages), `categories` (each an
`id` in capitals, a short `label`, the student's `definition`),
`polarities` (default `["very_negative","negative","positive","very_positive"]`;
add `"neutral"` only if they want it), `max_opinion_words` (6). Leave
`reinforcers` out to use the default list in `absa.py`, or write their own
list if they disagreed with it. Record the filled-in sentence under
**Our categories** in `experiment.md`. Run `split` again so the guard terms apply.

## Phase 2: predict, by hand

Before Claude annotates anything, each group annotates **one** review by
hand: the shortest. Show its numbered sentences from
`work/<id>.sentences.json`. For each judgment they find, they tell you: the
sentence number, the category, the exact words that judge, and the polarity.

Record their answers, exactly as given, in `hand/<id>.json` (same shape as in
`references/annotation.md`, `"annotator": "hand: <their names>"`). You are a
scribe here: do not correct, suggest, complete or rank their choices. If they
quote words that are not in the sentence, say so and let them fix it.

## Phase 3: Claude annotates, absa.py checks

Read `references/annotation.md`; it is the annotator's contract. Annotate
each review in a **fresh subagent** that receives only that file,
`codebook.json` and `work/<id>.sentences.json`, and writes
`tuples/<id>.json`. The subagent must not see `hand/` or this conversation,
so the comparison in Phase 4 is fair. If subagents are unavailable, annotate
here and write under **Notes** in `experiment.md` that the annotator saw the
students' hand labels first.

Report counts only (tuples per review, by polarity), not the tuples
themselves, until Phase 4 is done.

Run `python3 absa.py check`. It re-reads every quote from the review text,
checks every label against the codebook, applies the intensity rule, drops
duplicates, and writes `tuples.csv` and `check_report.md`. Show the student
the summary line and explain that it checks **form**, not whether a reading is
right. Fix errors only by rereading the sentence. If a judgment cannot be
quoted in the word limit, drop it and list it under **Dropped** in
`experiment.md`. Never raise `max_opinion_words`, edit `absa.py`, or loosen a
quote to make an error pass.

## Phase 4: disagree with the machine

```sh
python3 absa.py agree hand/<id>.json tuples/<id>.json
```

compares the students' annotation of that review with Claude's: which
sentences each picked, which (sentence, category) pairs both found, and where
the polarity differs. With so few tuples, read the rows rather than the
percentages. For two or three disagreements, ask: who is right, and what in
the sentence decides it? Record the answers under **Where we disagree with
Claude** in `experiment.md`.

Say once what this is: a tiny inter-annotator agreement exercise. A study
would have two people annotate a sample independently and report Cohen's
kappa or Krippendorff's alpha. A model agreeing with itself on a rerun shows
stability, not correctness.

## Phase 5: chart and two minutes

```sh
python3 absa.py chart
open results.html            # WSL: explorer.exe "$(wslpath -w results.html)"
```

`results.html` shows what the critics judged, where the praise ran out, each
review's net score next to its verdict, and every opinion with its sentence.
Before they present, have them write **What this chart conceals** in
`experiment.md` (five reviews, their sample, their codebook) and rerun
`chart` so it appears on the page. Small categories are small: point at the
`n` column.

Their two minutes: the film and their categories; one thing the chart shows;
one disagreement with Claude, with the sentence; what the chart conceals.

## Phase 6: the menu (after the workshop)

Only when the instructor releases it, or the student asks after presenting,
read `references/menu.md`: the SemEval convention, SentEMO's hotel and airline
codebooks, earlier film schemas, the instructor's *Parasite* categories and
the hard-case rules. Ask what they missed and what they invented that nobody
else has. Then change **one** decision in `codebook.json`, rerun `check` and
`chart`, and compare the two pages. Record both runs under **Second run**.

## Sharing, and what stays local

The review texts are copyrighted. They stay in `reviews/` and `work/` on the
student's machine; `.gitignore` already excludes both in case the folder ever
moves into a repository. What can be shown in class: `results.html`, which
quotes short spans and links to the originals. Do not commit or upload the
review files.

## Finish by taking stock

Nothing is committed or pushed. Show the student what is in `~/cms-lab/absa/`:
`codebook.json`, `hand/`, `tuples/`, `tuples.csv`, `check_report.md`,
`results.html` and `experiment.md`, and make sure `experiment.md` names what
each run showed. Record any library, codebook or idea they borrowed, from a
paper or a classmate, under **Borrowed**. To pick up later:
`cd ~/cms-lab && claude`, then `/cms-lab:absa`. For a final project at
corpus scale, `references/scaling-up.md` walks from five reviews to a hundred,
with the traps the instructor fell into.

If a command fails, show its actual error. Do not invent tuples, numbers or a
successful run. If a review cannot be read, the group works with four.
