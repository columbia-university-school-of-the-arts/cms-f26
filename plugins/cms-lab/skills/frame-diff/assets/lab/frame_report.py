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
prediction, from pixels it has already decoded. The encoder makes
the same guess by the same rules, so the guess itself is never stored. What
is stored is which guess to make, and how far the guess was wrong.

  Copied (inter prediction). The guess is a block from the previous frame.
  A motion vector says where: an offset such as "5 1/4 pixels left, 2 up",
  in quarter pixels. A block that did not move is a copy with a vector of
  zero.

  Drawn (intra prediction). The guess is built from the pixels already
  decoded just above and to the left of the block, in the same frame. The
  encoder uses this where nothing in the previous frame matches: at a cut,
  or where something enters the shot.

Residual. The difference between the guess and the real block, compressed.
The decoder adds it to the guess. A block whose guess is close enough gets no
residual at all (a "skip" block) and costs almost nothing.

Why copying is cheap. Describing a block's 256 pixels in three channels
typically costs hundreds of bits even after compression. A motion vector is two small
numbers, stored as its difference from the neighbouring blocks' vectors, so
when a whole region moves together, as in a camera pan, each vector costs a
few bits. A residual describes only how a copy differs from the real block,
which is usually small and smooth, and compresses far better than the block.

What the panels show. framediff.py decodes each P-frame against a flat gray
frame instead of the frame before it. Copied blocks then copy gray, so their
prediction disappears and only the residual is left. Drawn blocks are
predicted from their own frame, so they come out close to whole; where their
neighbours were copied blocks, the guess starts from gray and the block comes
out partly wrong. The "stored" panels therefore show the
residuals and the drawn blocks. The motion-vector panel shows the copies. The
prediction panel is the decoded frame minus what was stored: the decoder's guess,
before the residual was added (exact for copied blocks, apart from H.264's
smoothing of block edges after the residual is added).
Motion vectors are the encoder's choice of the cheapest block to copy, not a
measurement of how things moved: on flat areas many blocks match equally well,
and the arrows can point anywhere.
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

SINGLE_ROW = {"header_h": 84, "timeline_h": 320,      # framediff.py's layout when
              "sources": [["dec", "heat", "mv"]]}     # no .json was written beside it


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
