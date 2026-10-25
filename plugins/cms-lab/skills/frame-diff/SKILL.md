---
name: frame-diff
description: "Show what a video encoder stores for each frame and how the decoder rebuilds it: framediff.py re-encodes the student's clip as P-frames and renders labeled panels (decoded video, motion vectors, what each frame sent, the decoder's prediction, the previous frame) over a timeline of bytes stored per frame, then opens the result in mpv to step forward and back one frame at a time. frame_report.py measures single frames and explains the terms. Works in ~/cms-lab/frame-diff, not in a repository."
---

# Most of a frame is the last frame

Help the student see what a video encoder stores and how a decoder rebuilds a
picture from it. In most frames the encoder sends very little: the decoder
predicts each block by copying from the frame before, and the file carries the
instructions for that copy and a correction. `framediff.py` shows that data
directly. The student predicts, runs, then steps through the result in mpv
one frame at a time. Students have Claude Code but may be new to it: say what
each command does in one sentence before running it.

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
`frame_report.py` over the old ones only after the student agrees, and keep
their `experiment.md` and `out/`.

The project installs its two Python packages (numpy, matplotlib) into its own
folder:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
```

## What the panels are

The script makes its own H.264 encode of the clip on purpose: one flat gray
keyframe, then every frame of the clip as a P-frame, with no B-frames and no
new keyframes at cuts. The student's download had its own encoder and
settings; this is a controlled copy, so what they see is one encoder's
choices, made visible. Each P-frame is decoded twice: normally, and against
the gray keyframe instead of the frame before it. Blocks the encoder only
copied then copy gray, so what is left is what the frame itself sent.

| Panel | What it shows |
| --- | --- |
| decoded video | the encode, as a viewer sees it |
| motion vectors | the encoder's arrows over the decoded video: "copy this block from there" |
| sent per pixel | a heat map of what the frame sent: black where the encoder only copied, brighter the more it sent, on a log scale |
| sent, amplified | the same data in colour, its distance from gray multiplied by `--gain` (default 4) |
| prediction | what the decoder built before adding what was sent: the decoded frame minus what was sent |
| previous frame | the decoded frame the prediction copies from (for frame 0, the gray keyframe) |

`--view` picks the panels:

| `--view` | Panels |
| --- | --- |
| `heat` (default) | decoded video, sent per pixel, motion vectors |
| `amplified` | decoded video, sent amplified, motion vectors |
| `both` | decoded + motion vectors, sent amplified, sent per pixel |
| `prediction` | prediction, + sent amplified, = decoded video |
| `all` | previous frame (n−1), decoded + motion vectors (n), sent per pixel (n), above prediction (n), + sent amplified (n), = decoded frame (n) |

`all` reads top left to bottom right as the decoder's steps: pieces of the
previous frame, moved by the motion vectors, make the prediction; what was
sent is added to it; the result is the decoded frame. It is the only view
that shows two frames, which is why its labels say which. Its video is
1920x1208, so it may need full screen.

The timeline's top strip is the bytes stored for each frame; frame 0 has
nothing to copy from, so it is labelled rather than drawn to scale. The bottom
strip is the mean change in each colour channel from the frame before.

Before the first run, `frame_report.py --explain` prints these definitions
(blocks, prediction, motion vectors, residuals, why copying is cheap). Read
it with the student rather than paraphrasing it from memory.

## Step 1: the test clip

Before any film, run the built-in test. It makes `framediff_test.mp4`, four
seconds of a moving test pattern, a hard cut, then three seconds of a zooming
Mandelbrot fractal, and processes it:

```sh
.venv/bin/python framediff.py --make-test -o out/framediff_test_framediff.mp4 --view all
```

First ask the student what "sent per pixel" will show during the test
pattern, and what it will show at the cut. Then open the result (Step 4). At
2 s the heat map is almost all black: the bars do not move, so the encoder
copies them and sends only the moving line and the checkerboard. At frame 120
(4 s) the heat map lights up across the whole frame and the top strip spikes;
the prediction is nearly empty gray, apart from one blue block the encoder
copied from the colour bars anyway, which shows the wrong colour until what
was sent corrects it. If none of this appears, something is wrong with the
install; show the error rather than continuing.

## Step 2: the student's clip

Ask which clip they are using: usually this week's clip from Courseworks, or
their own. If `~/cms-lab/scene-detect/media/` already holds it, copy it into
`media/` here rather than downloading again. Otherwise download it with the
command in the scene-detect skill's `references/setup.md`, into `media/`.
Record the clip and its source in `experiment.md`.

Processing runs at about real time for 720p video, so a three-minute clip
takes about three minutes, and the output is large (around 100 MB; more for
`--view all`). For a first look, cut an excerpt of 20 to 30 seconds:

```sh
ffmpeg -ss 00:00:40 -t 25 -i media/CLIP.mp4 -c:v libx264 -crf 18 -c:a aac media/CLIP_excerpt.mp4
```

Before running, ask the student to write a prediction in `experiment.md`:
which moments will cost the most bytes, where the heat map will stay black
while the picture plainly changes, and what a slow camera move will do.

## Step 3: run

```sh
.venv/bin/python framediff.py media/CLIP_excerpt.mp4 -o out/CLIP_excerpt_framediff.mp4 --view all
```

Give a long-running command a timeout of ten minutes, or run it in the
background and check on it; do not let the shell's default time limit kill it
part way, which leaves a broken MP4. Beside the video the script writes a CSV,
one row per frame (time, frame type, bytes stored, share copied, mean change
in R, G and B), and a small `.json` describing the layout, which
`frame_report.py` reads.

`--crf` (default 23, range 0 to 51) is the encoder's quality setting. A
higher number lets it send less, so more of the heat map goes black and the
bytes fall; a lower one makes it send more. `--gain` changes only how strongly
the amplified panel is boosted. Change one setting per run and save each
output under its own name.

## Step 4: open it in mpv

When the script finishes, open the output in mpv, paused, with the frame
number on screen. Run it in the background so this session stays free:

```sh
nohup mpv --pause --keep-open=yes --osd-level=3 --osd-status-msg='frame ${estimated-frame-number}   ${time-pos}' out/CLIP_excerpt_framediff.mp4 >/dev/null 2>&1 &
```

Tell the student the keys: `.` one frame forward, `,` one frame back, space
to play or pause, `[` and `]` to slow down or speed up, `q` to quit. The
frame number on screen is the CSV's `frame` column.

Inside WSL, mpv opens a window only on Windows 11 (WSLg). If no window
appears, tell the student to open the file from Windows instead:
`explorer.exe out` opens the folder.

## Step 5: read it, one frame at a time

When the student finds a frame worth discussing, measure it:

```sh
.venv/bin/python frame_report.py out/CLIP_excerpt_framediff.mp4 120 121
```

For each frame it prints the bytes stored against the clip's median and the
share of the frame copied or sent, and saves every panel as a PNG in
`out/CLIP_excerpt_framediff_frames/` (named by row and panel, such as
`frame_00120_row2_pred.png`) for the student's notes or slides. "Copied"
counts pixels the frame's own data moves less than 6 levels from gray, so a
block with a very small correction counts as copied too.

Things to look for together:

- **The prediction.** Step across a fast movement and compare the previous
  frame, the prediction and the decoded frame. Where the prediction is a smear,
  nothing in the previous frame matched, and what was sent fills it in.
- **Change the encoder ignored.** A background can visibly shift in the
  decoded video while the heat map stays black there. The encoder judged a
  copy close enough and sent nothing; the decoded picture is the copy.
  Raising `--crf` makes this happen more often.
- **Cuts and flashes.** A spike in the top strip, a heat map lit across the
  frame, and an empty prediction: there was nothing to copy from.
- **Motion that costs little.** A camera pan can be almost free: arrows across
  the whole frame, a dark heat map. The encoder moves blocks rather than
  redrawing them.
- **Arrows that are not motion.** On flat areas many blocks match equally
  well, so motion vectors can point anywhere. Ask where the arrows follow what
  moves and where they only mark a cheap copy.
- **Bytes against change.** The two strips mostly rise together, but not
  always. Ask the student to find a frame where the colour change is large and
  the bytes are small, or the reverse, and explain it with the panels.

Have the student note two or three frames worth showing in `experiment.md`
with frame numbers and `frame_report.py`'s numbers, and compare them with
their prediction.

## Finish by taking stock

Nothing is committed or pushed. Show the student what is in
`~/cms-lab/frame-diff/`: `experiment.md`, each output video, CSV and layout
file under `out/`, saved frames, and the clip under `media/`. Make sure
`experiment.md` names every run and what it showed. To pick up later:
`cd ~/cms-lab && claude`, then `/cms-lab:frame-diff`.

If a run or install fails, show its actual error. Do not invent a result or
substitute a clip the student did not choose.
