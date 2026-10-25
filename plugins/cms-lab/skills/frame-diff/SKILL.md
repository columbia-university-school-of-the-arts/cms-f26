---
name: frame-diff
description: "Show what changes from one frame to the next: framediff.py renders the student's clip as three labeled panels (original, changed pixels, unchanged pixels) over a per-channel change timeline with the encoder's I-frames marked, then opens the result in mpv to step forward and back frame by frame. Works in ~/cms-lab/frame-diff, not in a repository."
---

# Most of a frame is the last frame

Help the student see what a video encoder sees: in most frames, most pixels
barely change, and compression spends its bits on the rest. `framediff.py`
makes that visible. The student predicts, runs, then steps through the result
in mpv one frame at a time. Students have Claude Code but may be new to it:
say what each command does in one sentence before running it.

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
place to save their changes.

The project installs its two Python packages (numpy, matplotlib) into its own
folder:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
```

## Step 1: the test clip

Before any film, run the built-in test. It makes `framediff_test.mp4`, four
seconds of a moving test pattern, a hard cut, then three seconds of a zooming
Mandelbrot fractal, and processes it:

```sh
.venv/bin/python framediff.py --make-test -o out/framediff_test_framediff.mp4
```

First ask the student what the timeline should look like: where a spike
should be, and what the line should do the rest of the time. Then open the
result (Step 4). The cut at 4 s should be one tall spike with an I-frame line
on it. If it is not, something is wrong with the install; show the error
rather than continuing.

## Step 2: the student's clip

Ask which clip they are using: usually this week's clip from Courseworks, or
their own. If `~/cms-lab/scene-detect/media/` already holds it, copy it into
`media/` here rather than downloading again. Otherwise download it with the
command in the scene-detect skill's `references/setup.md`, into `media/`.
Record the clip and its source in `experiment.md`.

Processing runs at about real time for 720p video, so a three-minute clip
takes three to four minutes and the output is large (over 100 MB). For a
first look, cut an excerpt of 20 to 30 seconds:

```sh
ffmpeg -ss 00:00:40 -t 25 -i media/CLIP.mp4 -c:v libx264 -crf 18 -c:a aac media/CLIP_excerpt.mp4
```

Before running, ask the student to write a prediction in `experiment.md`:
where they expect spikes, where they expect the "changed" panel to be nearly
black, and what grain or a slow camera move will do.

## Step 3: run

```sh
.venv/bin/python framediff.py media/CLIP_excerpt.mp4 -o out/CLIP_excerpt_framediff.mp4
```

Give a long-running command a timeout of ten minutes, or run it in the
background and check on it; do not let the shell's default time limit kill it
part way, which leaves a broken MP4. The script also writes
`out/CLIP_excerpt_framediff.csv`, one row per frame: time, frame type (I, P
or B), mean change in each colour channel, and percentage of pixels changed.

`--threshold` (default 8, out of 255) sets how much a pixel must change to
count as changed. Grainy or low-light footage often needs 15 to 25. Change it
one run at a time and save each output under its own name.

## Step 4: open it in mpv

When the script finishes, open the output in mpv, paused, with the frame
number on screen. Run it in the background so this session stays free:

```sh
nohup mpv --pause --keep-open=yes --osd-level=3 --osd-status-msg='frame ${estimated-frame-number}   ${time-pos}' out/CLIP_excerpt_framediff.mp4 >/dev/null 2>&1 &
```

Tell the student the keys: `.` one frame forward, `,` one frame back, space
to play or pause, `[` and `]` to slow down or speed up, `q` to quit. The
frame number on screen matches the CSV's `frame` column to within a frame.

Inside WSL, mpv opens a window only on Windows 11 (WSLg). If no window
appears, tell the student to open the file from Windows instead:
`explorer.exe out` opens the folder.

## Step 5: read it

Look at the timeline together, then step to the moments it points to:

- The yellow dashed lines are where the encoder placed full images
  (I-frames). On a YouTube download they usually fall every few seconds,
  whether or not there is a cut. Ask why an encoder would do that.
- A spike in the top strip and a bottom strip near 100% is a cut or a flash.
  Step across it with `,` and `.`.
- The "unchanged" panel is what the encoder can copy almost for free from
  the previous frame; the "changed" panel is what it has to pay for.
  Together they rebuild the original exactly.
- On black-and-white footage the R, G and B lines lie on top of one another,
  and blue, drawn last, hides the others. That is the footage, not a bug.

Have the student note two or three frames worth showing in `experiment.md`
with frame numbers, and compare them with their prediction.

Be honest about what the picture is. The panels are computed from decoded
pixels. The encoder does not store a P-frame as a picture of differences: it
stores motion vectors (copy this block from there) and a residual correcting
the prediction. To show the encoder's own motion vectors, re-encode without
B-frames and draw them:

```sh
ffmpeg -i media/CLIP_excerpt.mp4 -c:v libx264 -g 48 -bf 0 -crf 23 -an out/teach.mp4
ffmpeg -flags2 +export_mvs -i out/teach.mp4 -vf codecview=mv=pf -c:v libx264 -crf 18 out/teach_mv.mp4
```

## Finish by taking stock

Nothing is committed or pushed. Show the student what is in
`~/cms-lab/frame-diff/`: `experiment.md`, each output video and CSV under
`out/`, and the clip under `media/`. Make sure `experiment.md` names every
run and what it showed. To pick up later: `cd ~/cms-lab && claude`, then
`/cms-lab:frame-diff`.

If a run or install fails, show its actual error. Do not invent a result or
substitute a clip the student did not choose.
