---
name: frame-diff
description: "Show what a video encoder actually stores for each frame: framediff.py re-encodes the student's clip as P-frames and renders three labeled panels (the decoded video, each frame's own data decoded against gray, the encoder's motion vectors) over a timeline of bytes stored per frame and per-channel change, then opens the result in mpv to step forward and back frame by frame. frame_report.py measures single frames. Works in ~/cms-lab/frame-diff, not in a repository."
---

# Most of a frame is the last frame

Help the student see what a video encoder stores. In most frames the encoder
sends almost nothing: it copies blocks from the frame before, moves some of
them, and pays only for corrections and for what it cannot find. `framediff.py`
shows that data directly rather than a difference computed from pixels. The
student predicts, runs, then steps through the result in mpv one frame at a
time. Students have Claude Code but may be new to it: say what each command
does in one sentence before running it.

## Where the work lives

`~/cms-lab/frame-diff/`, a plain local folder. Not the fleet repository: no
clone, fork, commit or push. If Claude Code is not running inside
`~/cms-lab`, stop and give the student this line, then have them rerun
`/cms-lab:frame-diff`:

```sh
mkdir -p ~/cms-lab && cd ~/cms-lab && claude
```

The machine should already be ready: `/cms-lab:init` installs the tools and
writes `~/cms-lab/lab-setup.md`. Check `ffmpeg -version`, `ffprobe -version`,
`python3 --version` (3.10 or later) and `mpv --version`. If FFmpeg or Python
is missing, stop and send the student to `/cms-lab:init`. If only mpv is
missing, carry on; the video still plays in QuickTime or VLC, which step
forward but not back. Mention `/cms-lab:init` for later.

Copy `assets/lab/` beside this skill to `~/cms-lab/frame-diff/` only if that
folder does not exist. On later runs, read `experiment.md` and continue; never
overwrite the student's notes. The installed plugin is a template, not the
place to save their changes. If the folder exists from version 0.7 (its
`framediff.py` mentions `--threshold`), copy the new `framediff.py` and
`frame_report.py` over the old script only after the student agrees, and keep
their `experiment.md` and `out/`.

The project installs its two Python packages (numpy, matplotlib) into its own
folder:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
```

## What the three panels are

Explain this before the first run, in your own words:

- **decoded video**: the script's own H.264 encode of the clip, as a viewer
  sees it. The script makes this encode on purpose: one flat gray keyframe,
  then every frame of the clip as a P-frame, with no B-frames and no new
  keyframes at cuts. The student's download had its own encoder and settings;
  this is a controlled copy, so what they see is one encoder's choices, made
  visible.
- **what each frame stores**: each P-frame decoded on its own, predicting from
  the gray keyframe instead of from the frame before it. Blocks the encoder
  only copied come out gray, because it copied gray. What it paid to send
  shows on top: corrections, and blocks drawn from scratch.
- **motion vectors**: the encoder's arrows, drawn over the decoded video. Each
  says "copy this block from there in the previous frame".

The timeline's top strip is the bytes stored for each frame; frame 0 has
nothing to copy from, so it is labelled rather than drawn to scale. The bottom
strip is the mean change in each colour channel from the frame before.

## Step 1: the test clip

Before any film, run the built-in test. It makes `framediff_test.mp4`, four
seconds of a moving test pattern, a hard cut, then three seconds of a zooming
Mandelbrot fractal, and processes it:

```sh
.venv/bin/python framediff.py --make-test -o out/framediff_test_framediff.mp4
```

First ask the student what the middle panel will show during the test
pattern, and what it will show at the cut. Then open the result (Step 4). At
2 s the middle panel is almost all gray: the bars do not move, so the encoder
never sends them again. At frame 120 (4 s) it is the whole fractal, and the
top strip spikes. One block in the middle of that frame comes out the wrong
colour: the encoder copied it from the colour-bars frame and corrected it, and
against gray only the correction shows. If none of this appears, something is
wrong with the install; show the error rather than continuing.

## Step 2: the student's clip

Ask which clip they are using: usually this week's clip from Courseworks, or
their own. If `~/cms-lab/scene-detect/media/` already holds it, copy it into
`media/` here rather than downloading again. Otherwise download it with the
command in the scene-detect skill's `references/setup.md`, into `media/`.
Record the clip and its source in `experiment.md`.

Processing runs at about real time for 720p video, so a three-minute clip
takes about three minutes and the output is large (around 100 MB). For a
first look, cut an excerpt of 20 to 30 seconds:

```sh
ffmpeg -ss 00:00:40 -t 25 -i media/CLIP.mp4 -c:v libx264 -crf 18 -c:a aac media/CLIP_excerpt.mp4
```

Before running, ask the student to write a prediction in `experiment.md`:
which moments will cost the most bytes, where the middle panel will stay gray
while the picture plainly changes, and what a slow camera move will do.

## Step 3: run

```sh
.venv/bin/python framediff.py media/CLIP_excerpt.mp4 -o out/CLIP_excerpt_framediff.mp4
```

Give a long-running command a timeout of ten minutes, or run it in the
background and check on it; do not let the shell's default time limit kill it
part way, which leaves a broken MP4. The script also writes
`out/CLIP_excerpt_framediff.csv`, one row per frame: time, frame type, bytes
stored, and the mean change in R, G and B.

`--crf` (default 23, range 0 to 51) is the encoder's quality setting. A
higher number lets it send less, so more of the middle panel stays gray and
the bytes fall; a lower one makes it send more. Try 18 and 35 on the same
excerpt, one run at a time, each saved under its own name.

## Step 4: open it in mpv

When the script finishes, open the output in mpv, paused, with the frame
number on screen. Run it in the background so this session stays free:

```sh
nohup mpv --pause --keep-open=yes --osd-level=3 --osd-status-msg='frame ${estimated-frame-number}   ${time-pos}' out/CLIP_excerpt_framediff.mp4 >/dev/null 2>&1 &
```

Tell the student the keys: `.` one frame forward, `,` one frame back, space
to play or pause, `[` and `]` to slow down or speed up, `q` to quit. The
frame number on screen matches the CSV's `frame` column.

Inside WSL, mpv opens a window only on Windows 11 (WSLg). If no window
appears, tell the student to open the file from Windows instead:
`explorer.exe out` opens the folder.

## Step 5: read it, one frame at a time

When the student finds a frame worth discussing, measure it:

```sh
.venv/bin/python frame_report.py out/CLIP_excerpt_framediff.mp4 120 121
```

For each frame it prints the bytes stored against the clip's median and the
share of the frame the encoder copied, and saves the three panels as PNGs in
`out/CLIP_excerpt_framediff_frames/` for the student's notes or slides.
"Copied" is read from the middle panel: a block counts as copied when it is
within 6 of flat gray, so a block that got a very small correction counts too.

Things to look for together:

- **Change the encoder ignored.** A background can visibly shift in the
  decoded video while the middle panel stays gray there. The encoder judged a
  copy close enough and sent nothing; the decoded picture is the copy. Raising
  `--crf` makes this happen more often.
- **Cuts and flashes.** A spike in the top strip and a middle panel full of
  picture: there was nothing to copy from.
- **Motion that costs little.** A camera pan can be almost free: arrows across
  the whole frame, little in the middle panel. The encoder moves blocks rather
  than redrawing them.
- **Bytes against change.** The two strips mostly rise together, but not
  always. Ask the student to find a frame where the colour change is large and
  the bytes are small, or the reverse, and explain it with the panels.

Have the student note two or three frames worth showing in `experiment.md`
with frame numbers and `frame_report.py`'s numbers, and compare them with
their prediction.

## Finish by taking stock

Nothing is committed or pushed. Show the student what is in
`~/cms-lab/frame-diff/`: `experiment.md`, each output video and CSV under
`out/`, saved frames, and the clip under `media/`. Make sure `experiment.md`
names every run and what it showed. To pick up later: `cd ~/cms-lab && claude`,
then `/cms-lab:frame-diff`.

If a run or install fails, show its actual error. Do not invent a result or
substitute a clip the student did not choose.
