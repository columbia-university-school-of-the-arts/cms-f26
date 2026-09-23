<!--
Drafted 2026-09-23.
Concept half from docs/rk-lesson-outlines.md, Week 3, which reads RK's outline
at Drive modifiedTime 2026-08-07T14:13Z (snapshot of 2026-09-12; not re-synced
before this draft). Practice half from the cms-lab plugin in the hub, commit
2f015e4, renamed in 13f4024: the scene-detect skill, its setup reference, and its ingredient shelf.
This replaces the Week 3 practice column of the 2026-09-06 artifact-ladder
spec: the Rocky montage stands in for RK's bigger_boat.mp4, the hand pass is
in the browser rather than Cowork, and the OpenAlex/Crossref raw call and the
artifact's metadata field are not on tonight's sheet. Timings are a draft.
-->

# Week 3: a cut is a decision

Coding for Media Studies, Wednesday 23 September. Version 2026.09.23.

Tonight you measure a film. You watch a three-minute montage, mark its cuts by
hand, and write down a rule for what counts as one. Then Claude Code builds
that rule into a small app on your own machine: a timeline of scores, a
threshold you can drag, shot lengths, and an average. You test the rule
against the footage, find where it fails, and only then see how other people
have built the same thing.

The point is not a good detector. The point is that "a cut" had to be defined
before anything could count it, and the definition is yours.

**Bring** your laptop with last week's install working, your repository
cloned, and headphones.

---

## The concept hour (6:00 to 7:00)

Two readings this week. Moretti and Sobchuk, "Hidden in Plain Sight," is the
concept reading. Arnold and Tilton, *Distant Viewing*, chapter 3, is the
practice one.

The hour's real subject is **historiography**: what a chart claims about the
past, and what it hides.

- **Average shot length** is the worked example, and it has a history of its
  own. Barry Salt proposed it in 1974. Yuri Tsivian built Cinemetrics in 2005.
  The measure has moved from a stopwatch to software such as PySceneDetect.
- Arnold and Tilton supply the turn: human visual concepts do not arrive
  already packaged as computational features. To count cuts, someone has to
  decide in computable terms what a cut is, and that decision settles what
  becomes information.
- **The regression line interprets; it does not only display.** Plot shot
  lengths across film history and a line shows a smooth decline. The dots
  show something else: a sharp break at the coming of sound, then a slower
  drift. Averages also hide genre. Action films cut faster than comedies, so
  a corpus that tilts toward action shows a change in editing that no editor
  made.
- Moretti and Sobchuk's point in general form: a regular statistical trend
  can come from thoroughly irregular historical forces.

Hold on to that last point. At 8:00 you will produce an average shot length
of your own.

---

## Compare (7:10 to 7:20)

Last week's homework, in the room. Which of the three outside sources was
invented, and how you knew. What `git status` said before and after your
commit. One citation Claude Code could not find, and what you did about it.

---

## By hand first (7:20 to 7:35)

The clip is the training montage from *Rocky* (three minutes, on YouTube; the
link is on Courseworks). Watch it in your browser, with sound. Write down the
time of every cut you see, to the second. Mark the ones you are not sure of.

Then write one sentence: **what visible change made you call it a cut?** And
a second: **what might fool that rule?**

Keep both sentences. They become the code. There is no menu of methods yet,
on purpose: invent before you see what others invented.

---

## Install the workshop (7:35 to 7:50)

In Terminal, go to your repository and start Claude Code:

    cd ~/cms-f26-fleet-YOUR-USERNAME
    claude

Then install this week's plugin and start it:

    /plugin marketplace update cms-f26
    /plugin install cms-lab@cms-f26
    /cms-lab:scene-detect

If the marketplace update says `cms-f26` is not added, run
`/plugin marketplace add columbia-university-school-of-the-arts/cms-f26`
first. If `/cms-lab:scene-detect` is not recognised, type `/exit`, run `claude`
again, and retry.

The skill copies a small lab into `experiments/scene-detect/` in your repository.
It then walks you through three installs and one download: Python, FFmpeg
and Deno through Homebrew, a few Python packages into a folder of their own
(`.venv`), and the clip itself, fetched with a tool called `yt-dlp`. Read each
command before you agree to it; Claude will say what each does in a sentence.

*Delegation* again. You are letting a tool fetch a film onto your disk. The
video and anything cut from it stay on your machine and never go into git.

**On Windows**, all of this runs inside WSL, as last week. The app opens in
your Windows browser.

**If the download fails**, read the error out loud to us. Do not retry it
over and over. Pair with a neighbour whose download worked, or keep marking
cuts in the browser while we look.

---

## Your rule, as code (7:50 to 8:20)

Tell Claude your two sentences. It records them, and your hand-marked
timestamps, in `experiment.md` before it writes any code.

Before the video, test the rule on something tiny. Claude will ask what your
rule should say about two identical frames, and about one small change you
choose. Work out the answer together by hand, then run it. If the code and
the arithmetic disagree, one of them is wrong, and finding out which is the
exercise.

Then Claude builds your rule into `detector.py` and starts the app:

    .venv/bin/python -m streamlit run app.py --server.address 127.0.0.1

It prints a local address. Open it in your browser. You will see the clip, a
line of change scores over time, a threshold you can drag, the proposed cuts
in red and yours in dashed green, a table of shots, and **average shot
length**.

The average describes this excerpt, not the film. Its first and last shots
are cut off by the excerpt's edges.

---

## Check it against the footage (8:20 to 8:35)

A proposed cut is not a verified one. For each disagreement between the red
lines and the green:

- Open the frames on either side of it, and render a short clip across it.
  The app does both on request.
- Watch the whole clip again, too. Checking only what the rule proposed hides
  every cut it missed.

Write down one confirmed cut, one **false alarm**, one **missed cut**, and
anything you could not decide, with times. Your own marks are not the answer
key either; the montage has cuts that are hard to call. Change one setting at
a time, and press **Save** after each version you want to keep.

That is *Discernment* with a timeline: which of these is the rule, which is
the film, and which is you.

---

## The ingredient shelf (8:35 to 8:50)

Now we release the shelf. Tell Claude we have, and it opens the list of
ingredients a cut detector is made from: **where** to look in the frame, what
to **represent** it as, what **change** to measure, and how to **decide**. Each
comes with what it lets a rule notice and what it makes easier to miss.

Save your invented rule and its run first. Then build one new combination and
keep both. Fill in this sentence before any code is written:

> Look at ___ of the frame, represent it as ___, measure ___ between frames,
> and call it a cut when ___. Check the claim by ___.

BG's own detector is on the shelf as one worked example: changed pixels in
the centre of the frame. It is one choice, not the answer.

Anything you borrow, a library or an idea, gets a line in your ledgers:
`notes/INTEGRATIONS.md` for code, `notes/PATTERNS.md` for ideas. A
classmate's idea goes in the second with their name.

---

## The comparison, and your commit (8:50 to 9:00)

Last, PySceneDetect, the tool the reading's history ends on. Run it on the
same file and look at where it disagrees with you. It is not the ground truth
either. It is someone else's definition of a cut, packaged.

Then commit. Ask Claude to show you `git status` and what it plans to stage.
Code, `experiment.md`, and your saved runs go in. The video, the rendered
clips, and `.venv` stay out. Commit, push, and open your repository in the
browser to check.

Type `/exit` when done.

---

## Homework

1. Finish `experiment.md`, especially its last section: **what this average
   conceals**. How do your short and long shots differ? What happens to the
   average when one boundary moves? Commit it.
2. Save at least two contrasting runs, if you did not get there in the room,
   and say in `experiment.md` what you predicted each would do.
3. Pick one disagreement between your rule and PySceneDetect and explain it in
   three sentences. Bring the timestamp.

---

## For Week 4, be ready to say

Your rule in one sentence, and the cut it missed. What your average shot
length was, and one thing it hides. Where your definition and PySceneDetect's
parted, and whose you would trust for that cut.
