---
name: scene-detect
description: "Build and investigate an interactive shot-boundary detector for the CMS video workshop: invent a rule, tune sliders, inspect FFmpeg clips, and compare methods when the instructor releases them. Works in a local lab folder, ~/cms-lab/scene-detect, not in a repository."
---

# A cut is a decision

Help the student turn their own definition of a cut into a working, inspectable
artifact. Students have Claude Code installed but may be new to it. Explain
each command's purpose in one sentence.

## Where the work lives

The lab is a set of plain local folders, one per project, under `~/cms-lab/`.
This project's folder is `~/cms-lab/scene-detect/`. It is the student's own
workspace on their own machine: not their fleet repository, not a fork, and
nothing is pushed anywhere. Do not create a GitHub repository, clone, fork, or
commit for this workshop.

Claude Code should run from inside `~/cms-lab`. If the current directory is not
`~/cms-lab` or a folder under it, stop. Tell the student to type `/exit`,
then paste this line into the same Terminal, then run `/cms-lab:scene-detect`
again:

```sh
mkdir -p ~/cms-lab && cd ~/cms-lab && claude
```

If the student already started this workshop in `experiments/scene-detect/`
inside their fleet repository, continue there rather than moving their work.

## Phase 1: invent before encountering the menu

BG shares the clip through Courseworks: https://www.youtube.com/watch?v=-1tza4BxVfA.
Ask the student to watch it, mark a few
cuts by time, and state one rule in their own words. Ask what visible change
would count, and what might fool that rule. Wait for their answer. Do not
suggest named algorithms, open `references/approaches.md`, or install
PySceneDetect at this stage. The clip is downloaded by the student with
`yt-dlp`; there is no course-supplied MP4.

Read `references/setup.md` for the download and environment workflow. Copy
`assets/lab/` beside this skill into `~/cms-lab/scene-detect/`, only if that
destination does not exist. On later invocations inspect
and continue their work; never overwrite their detector. The installed plugin
is a template, not the place to save their changes.

Record the student's words and manual timestamps in `experiment.md` before
implementing their rule in `detector.py`. Carry forward the prior image-objects
exercise: predict before running, test on a tiny hand-checkable example, then
inspect the real output. Ask what the rule should return for two identical
small frames and for a student-chosen change; calculate the expected score
together and test it. Explain RGB values, coordinates, or aggregation only as
the chosen rule needs them. OpenCV frames are BGR, not RGB. Do not require
manual Python loops or revive the Colab/Gemini workflow.

The deliberately unimplemented
`score_pair` is the teaching task, not an error to silently fix with a default
algorithm. Name the method, explain its score units and slider ranges, and
add controls for parameters the rule actually uses. All scores must be finite
and higher must mean more change. If the rule needs temporal context, extend
the adapter explicitly; do not substitute a different rule to fit two frames.

Launch the provided Streamlit app locally. Show the student the full video,
score timeline, threshold, proposed boundaries, shot lengths and average shot
length. Explain that the first and last shots are truncated by this excerpt.
The average describes this clip, not the film.

## Phase 2: compose after BG releases the ingredients

Only when the student says BG has released the ingredient shelf or explicitly requests
this phase, read and show `references/approaches.md`. This is a teaching
sequence, not an access-control mechanism: the file is part of the plugin.

Save the invented rule and its run first. Define each ingredient the student
considers: where to look, representation, change measurement, aggregation and
decision rule. Let them compose a combination, not merely choose a complete
algorithm from a list. Explain units, meaningful controls and what each choice
can hide; ask them to predict its effect. Then implement their combination
using open-source libraries. Preserve earlier variants
(e.g. separate detector modules selected in the app), exposing each method's
meaningful parameters. The shelf is broad; nobody must use every ingredient. BG’s center-region
example illustrates one combination and does not replace the student’s choice.
Add new dependencies only for the selected ingredients. Record exact versions,
licenses and sources under **Borrowed** in `experiment.md`, code and ideas
alike, with a classmate's name when the idea is theirs. Credit the shared
interface too.

## Phase 3: tune, inspect, defend

Change one parameter at a time. Save at least two contrasting runs with the
rule, parameter values, code, dependency versions, source identity, score
series and shot table. The app writes this evidence to `runs/` only when the
student presses Save. Its boundary convention is the first frame of the new
shot; intervals are start-inclusive/end-exclusive. Threshold equality does
not trigger a cut. A minimum gap suppresses nearby detections; it is not
proof that short shots cannot exist.

Use FFmpeg to render actual shot clips and short windows spanning each cut.
The app does this on demand and re-encodes instead of snapping to keyframes.
Review full playback as well: inspecting only predicted cuts hides misses.
Write down confirmed cuts, false alarms, missed cuts, and ambiguous cases,
with timestamps. Manual marks are a reference to discuss, not unquestionable
truth. Compare identical source files; a different download may differ.

## Phase 4: final comparison

Only at the instructor's final comparison, introduce PySceneDetect. Follow
`references/approaches.md` for its source and comparison procedure. Run it on
the same local input; map its scene intervals to the same boundary convention.
Inspect disagreements using the same FFmpeg previews. Do not call its output
ground truth or replace the student's implementation with it.

## Finish by taking stock

Nothing is committed or pushed. Before the student stops, show them what is in
`~/cms-lab/scene-detect/`: their `detector.py` and any variants, `experiment.md`,
and each saved run under `runs/`. The video, rendered clips and `.venv` are
there too and stay there. Make sure `experiment.md` names every saved run and
what it showed. To pick up later: `cd ~/cms-lab && claude`, then
`/cms-lab:scene-detect`.

If a download or install fails, surface its actual error. Pair with a student
whose download worked or continue manual annotation in the browser; do not
invent a successful run or silently substitute another clip.
