#!/usr/bin/env python3
"""
frame_report.py: one frame of a framediff.py output, in numbers and pictures.

Usage:
    python3 frame_report.py out/clip_framediff.mp4 120
    python3 frame_report.py out/clip_framediff.mp4 120 121 122
    python3 frame_report.py --explain          # print the definitions below

For each frame number (the number mpv shows, and the CSV's `frame` column) it
saves every panel as a PNG in <video>_frames/, named by row and panel, and
prints what the encoder did with that frame:

  bytes stored   from the CSV, and how that compares with the clip's median
  copied         share of pixels the encoder only copied: the frame's own data
                 moves them less than 6 levels (of 255) from the gray reference
  corrected or   the rest: blocks the frame's stored data corrects, and
  redrawn        blocks drawn from scratch

"Copied" counts a pixel whose correction is very small as copied too, so it
is an upper bound on what the encoder stored nothing for.

Needs ffmpeg on PATH, and: pip install numpy matplotlib


HOW A P-FRAME IS BUILT

Blocks. The encoder cuts each frame into blocks: 16x16 pixels in H.264,
split down to 4x4 where the picture needs detail.

Every frame is built fresh. The decoder makes each new frame block by block.
Nothing is removed from the previous frame; each block of the new frame is
either copied or drawn.

Prediction. For each block, the decoder first makes a guess at it, its
prediction, from pixels it has already decoded. The encoder contains the same
decoder and makes the same guess by the same rules, so the guess itself is
never stored. What is stored is which guess to make, and how far the guess
was wrong. Prediction is a procedure the decoder runs, not data in the file:
the picture exists only once the decoder runs it over the previous frame.

  Copied (inter prediction). The guess is a block from the previous frame.
  A motion vector says where: an offset such as "5 1/4 pixels left, 2 up",
  in quarter pixels. A block that did not move is a copy with a vector of
  zero. The vector is stored in this frame's data and points back into the
  frame before.

  Drawn (intra prediction). The guess is built from the pixels already
  decoded just above and to the left of the block, in the same frame. The
  encoder uses this where nothing in the previous frame matches: at a cut,
  or where something enters the shot.

Residual. The difference between the guess and the real block, compressed.
The decoder adds it to the guess. A block whose guess is close enough gets no
residual at all (a "skip" block) and costs almost nothing.

Why copying is cheap. Describing a block's 256 pixels in three channels
typically costs hundreds of bits even after compression. A motion vector is
two small numbers, stored as its difference from the neighbouring blocks'
vectors, so when a whole region moves together, as in a camera pan, each
vector costs a few bits. A residual describes only how a copy differs from
the real block, which is usually small and smooth, and compresses far better
than the block.

Bytes. The last stage, the entropy coder, also predicts: it estimates how
likely each next bit is from the bits around it, and spends fewer bits on
what it expected. The "KB stored" numbers come out of that stage. No panel
shows it.

Motion vectors are the encoder's choice of the cheapest block to copy, not a
measurement of how things moved: on flat areas many blocks match equally
well, and the arrows can point anywhere.


WHAT THE PANELS SHOW

The encode. framediff.py makes its own H.264 encode of the clip: one flat
gray keyframe, then every frame of the clip as a P-frame, with no B-frames
and no new keyframes at cuts. It is a controlled copy, one encoder at one
setting (--crf), not the encode the clip was downloaded in.

The gray reference. Each P-frame is also decoded against the gray keyframe
instead of the frame before it. Copied blocks then copy gray, so their
prediction disappears and only the residual is left. Drawn blocks are
predicted from their own frame, so they come out close to whole; where their
neighbours were copied blocks, the guess starts from gray and the block comes
out partly wrong. What is left is what the frame itself stored: its
residuals and its drawn blocks.

  decoded video      the encode, as a viewer sees it.
  motion vectors     the encoder's arrows, drawn on the decoded frame (n),
                     each pointing back to where its block was copied from in
                     frame n-1. At a cut there are almost none: nothing in the
                     old shot was worth copying.
  stored per pixel   a heat map of what the frame stored: black where the
                     encoder only copied, brighter the further the frame's own
                     data moves a pixel from gray, on a log scale so that
                     corrections of 1 or 2 levels show beside whole redrawn
                     blocks. Brightness is not a byte count: a drawn block
                     whose colours happen to be near gray looks dark.
  stored, amplified  the same data in colour, its distance from gray
                     multiplied by --gain (default 4). In a typical frame most
                     pixels sit within a few levels of gray, which looks flat;
                     4x makes a 3-level correction show as 12. Large changes,
                     such as a block redrawn at a cut, clip to white or black.
  prediction         the decoded frame minus what was stored: the decoder's
                     guess before the residual is added. Close to exact for
                     copied blocks (H.264 smooths block edges after adding the
                     residual, which the subtraction cannot undo). For drawn
                     blocks it shows mostly gray, since nothing was copied.
  previous frame     the decoded frame n-1, which copied blocks come from. For
                     frame 0 it is the gray keyframe.

--view all is the one view that shows two frames, so its labels say which:
previous frame (n-1) on the top left, and (n) on the rest. Read it top left
to bottom right as the decoder's steps: pieces of the previous frame, moved
by the motion vectors, make the prediction; what was stored is added to it;
the result is the decoded frame.

The words. "Stored" is what the file holds for a frame beyond a copy of the
previous one. Codecs describe the same data as sent by the encoder and
received by the decoder, the language of transmission; in a file it is
stored, and the timeline measures it in bytes stored.
"""
import argparse
import csv
import json
import os
import subprocess
import sys

import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

SINGLE_ROW = {"header_h": 84, "timeline_h": 320,      # the layout of renders made before
              "sources": [["dec", "heat", "mv"]]}     # framediff.py wrote a .json beside them


def size_of(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0",
                          "-show_entries", "stream=width,height", "-of", "csv=p=0", path],
                         check=True, capture_output=True, text=True).stdout
    w, h = out.strip().split(",")[:2]
    return int(w), int(h)


def grab(path, n, w, h):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path,
                          "-vf", f"select=eq(n\\,{n})", "-fps_mode", "passthrough",
                          "-frames:v", "1", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                         check=True, capture_output=True).stdout
    if len(raw) < w * h * 3:
        raise SystemExit(f"frame {n} is past the end of {path}")
    return np.frombuffer(raw[:w * h * 3], np.uint8).reshape(h, w, 3)


def main():
    ap = argparse.ArgumentParser(description="Measure single frames of a framediff.py output.")
    ap.add_argument("video", nargs="?", help="an output of framediff.py")
    ap.add_argument("frames", nargs="*", type=int)
    ap.add_argument("--explain", action="store_true",
                    help="print how a P-frame is built, and what the panels show")
    args = ap.parse_args()
    if args.explain:
        print(__doc__[__doc__.index("HOW A P-FRAME IS BUILT"):].rstrip())
        return
    if not args.video or not args.frames:
        ap.error("give a framediff.py output and one or more frame numbers")

    csv_path = os.path.splitext(args.video)[0] + ".csv"
    if not os.path.exists(csv_path):
        raise SystemExit(f"{csv_path} not found: frame_report.py reads the CSV "
                         "that framediff.py writes beside its video")
    rows = list(csv.DictReader(open(csv_path)))
    if "copied_pct" not in rows[0]:
        raise SystemExit(f"{csv_path} comes from an older framediff.py; render the clip again")
    sizes = [int(r["bytes"]) for r in rows]
    median = float(np.median(sizes[1:] or sizes))

    layout_path = os.path.splitext(args.video)[0] + ".json"
    layout = json.load(open(layout_path)) if os.path.exists(layout_path) else SINGLE_ROW
    w, h = size_of(args.video)
    header_h, sources = layout["header_h"], layout["sources"]
    pw = w // 3
    ph = layout.get("panel_h", h - header_h - layout["timeline_h"])
    outdir = os.path.splitext(args.video)[0] + "_frames"
    os.makedirs(outdir, exist_ok=True)

    for n in args.frames:
        if not 0 <= n < len(rows):
            raise SystemExit(f"frame {n} is outside 0 to {len(rows) - 1}")
        img = grab(args.video, n, w, h)
        for r, row in enumerate(sources):
            y = r * (header_h + ph) + header_h
            for i, name in enumerate(row):
                panel = img[y:y + ph, i * pw:(i + 1) * pw]
                tag = f"row{r + 1}_{name}" if len(sources) > 1 else name
                plt.imsave(os.path.join(outdir, f"frame_{n:05d}_{tag}.png"), panel)
        r = rows[n]
        b, copied = int(r["bytes"]), float(r["copied_pct"])
        print(f"frame {n}: {b:,} bytes stored ({b / median:.1f}x the clip's median "
              f"of {median:,.0f}), t={float(r['time_s']):.2f}s; "
              f"{copied:.0f}% copied, {100 - copied:.0f}% corrected or redrawn")
    print(f"panels saved in {outdir}/", file=sys.stderr)


if __name__ == "__main__":
    main()
