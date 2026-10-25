#!/usr/bin/env python3
"""
framediff.py: show what a video encoder actually stores, frame by frame.

The script re-encodes the clip with H.264 as a flat gray keyframe followed
only by P-frames (every frame of the clip becomes a P-frame). It then decodes
each P-frame twice: normally, and against the gray keyframe instead of the
frame before it. What a frame shows against gray is what the encoder sent for
it (corrections, and blocks drawn from scratch); copied blocks copy gray.

Panels (--view picks which, in rows of three):

  decoded video     the encode, as a viewer sees it
  motion vectors    the encoder's own arrows: "copy this block from there"
  sent, amplified   what the frame sent, in colour, its distance from gray
                    multiplied by --gain
  sent per pixel    the same as a heat map: black where the encoder only
                    copied, brighter the more it sent, on a log scale
  prediction        what the decoder built before adding what was sent: the
                    decoded frame minus what was sent (exact for copied blocks
                    up to H.264's edge smoothing)
  previous frame    the decoded frame before this one, which the prediction
                    is copied from (for frame 0, the gray keyframe)

  --view heat        decoded | sent per pixel | motion vectors (default)
  --view amplified   decoded | sent, amplified | motion vectors
  --view both        decoded + motion vectors | sent, amplified | sent per pixel
  --view prediction  prediction | + sent, amplified | = decoded
  --view all         previous frame (n-1) | decoded + motion vectors (n) |
                     sent per pixel (n), above prediction (n) |
                     + sent, amplified (n) | = decoded frame (n)

Timeline: bytes the encoder stored for each frame, and the mean change in
each colour channel, with a playhead that follows the video.

Usage:
    python3 framediff.py input.mp4
    python3 framediff.py input.mov -o out.mp4 --view all --crf 30
    python3 framediff.py --make-test            # builds and processes a test clip

Needs ffmpeg + ffprobe on PATH, and: pip install numpy matplotlib
Also writes <output>.csv with the per-frame numbers, and <output>.json with
the layout, which frame_report.py reads.
"""
import argparse
import csv
import json
import os
import subprocess
import sys
import tempfile

import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

HEADER_H = 84          # label bar above the panels, in pixels (frame_report.py reads it)
TIMELINE_H = 320       # timeline strip below the panels, in pixels
AX_LEFT_PX = 90        # timeline plot margins, in pixels (fixed so the
AX_RIGHT_PX = 40       # playhead lines up with the plotted data)
BG = "#000000"
FG = "#d8d8d8"
CHANNEL_COLORS = {"R": "#ff4d4d", "G": "#3ddc84", "B": "#4d8dff"}
BYTES_COLOR = "#ffcc33"
# --view: rows of panels, left to right. Each panel is (source, label).
# Sources: dec (decoded), mv (motion vectors on decoded), amp (sent, amplified),
# heat (sent per pixel), pred (prediction), prev (previous decoded frame).
# Labels may use {gain}.
ROW_BOTH = [("mv", "decoded + motion vectors"), ("amp", "sent, amplified {gain}x"),
            ("heat", "sent per pixel")]
ROW_PREDICTION = [("pred", "prediction"), ("amp", "+ sent, amplified {gain}x"),
                  ("dec", "= decoded video")]
VIEWS = {
    "heat": [[("dec", "decoded video"), ("heat", "sent per pixel"), ("mv", "motion vectors")]],
    "amplified": [[("dec", "decoded video"), ("amp", "sent, amplified {gain}x"),
                   ("mv", "motion vectors")]],
    "both": [ROW_BOTH],
    "prediction": [ROW_PREDICTION],
    # Read top left to bottom right: pieces of the previous frame, moved by the
    # motion vectors, make the prediction; what was sent is added to it.
    # This is the one view that shows two frames, so its labels say which.
    "all": [[("prev", "previous frame (n\u22121)"), ("mv", "decoded + motion vectors (n)"),
             ("heat", "sent per pixel (n)")],
            [("pred", "prediction (n)"), ("amp", "+ sent, amplified {gain}x (n)"),
             ("dec", "= decoded frame (n)")]],
}
PIPED = ["amp", "heat", "pred", "prev"]   # panels computed in Python and piped, in this order
HEAT_MAX = 64          # levels from gray (0-255) that reach the top of the heat scale
COPY_TOL = 6           # within this many levels of gray, a pixel counts as copied


def run(cmd, **kw):
    return subprocess.run(cmd, check=True, **kw)


def probe(path):
    out = run(["ffprobe", "-v", "error", "-select_streams", "v:0",
               "-show_entries", "stream=width,height,avg_frame_rate",
               "-of", "json", path], capture_output=True).stdout
    s = json.loads(out)["streams"][0]
    num, den = s["avg_frame_rate"].split("/")
    fps = float(num) / float(den) if float(den) else 30.0
    return int(s["width"]), int(s["height"]), fps


def make_test_clip(path):
    """7 s test clip: 4 s of moving test pattern, a hard cut, 3 s of zooming
    Mandelbrot fractal. The cut forces the encoder to repaint the whole frame."""
    if os.path.dirname(path):
        os.makedirs(os.path.dirname(path), exist_ok=True)
    run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
         "-f", "lavfi", "-i", "testsrc2=s=1280x720:r=30:d=4",
         "-f", "lavfi", "-i", "mandelbrot=s=1280x720:r=30,trim=duration=3",
         "-f", "lavfi", "-i", "sine=d=7",
         "-filter_complex", "[0:v][1:v]concat=n=2:v=1[v]",
         "-map", "[v]", "-map", "2:a", "-c:v", "libx264", "-pix_fmt", "yuv420p",
         "-c:a", "aac", path])
    print(f"made test clip {path}", file=sys.stderr)


def encode_p_only(src, dst, pw, ph, fps, crf):
    """A gray keyframe, then the clip as P-frames only: no B-frames, no new
    keyframes at cuts, one reference frame, one slice per frame. Raw Annex B
    H.264, so frames can be cut apart and rearranged."""
    lead = f"color=c=0x808080:s={pw}x{ph}:r={fps:.6f}"
    run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
         "-f", "lavfi", "-i", lead, "-i", src,
         "-filter_complex",
         f"[0:v]trim=end_frame=1,format=yuv420p,setsar=1[g];"
         # Re-time frames one after another: keeps every source frame exactly
         # once (a frame-rate filter would duplicate frames on uneven timestamps)
         f"[1:v]scale={pw}:{ph},setpts=N/({fps:.6f}*TB),format=yuv420p,setsar=1[v];"
         f"[g][v]concat=n=2:v=1[o]",
         "-map", "[o]", "-an", "-r", f"{fps:.6f}",
         "-c:v", "libx264", "-preset", "veryfast", "-crf", str(crf), "-bf", "0",
         "-x264-params", "keyint=1000000:min-keyint=1000000:scenecut=0:ref=1:slices=1",
         "-bsf:v", "h264_mp4toannexb", "-f", "h264", dst])


def split_nals(data):
    """Annex B byte stream -> list of NAL units without their start codes."""
    starts, i = [], 0
    while True:
        j = data.find(b"\x00\x00\x01", i)
        if j < 0:
            break
        starts.append(j + 3)
        i = j + 3
    nals = []
    for k, s in enumerate(starts):
        e = starts[k + 1] - 3 if k + 1 < len(starts) else len(data)
        nal = data[s:e]
        while nal.endswith(b"\x00"):   # the extra zero of a 4-byte start code
            nal = nal[:-1]
        nals.append(nal)
    return nals


def pair_with_gray(src, dst):
    """Rewrite the stream as (gray keyframe, P-frame n) pairs. Decoded, each
    P-frame then predicts from gray rather than from the frame before it."""
    nals = split_nals(open(src, "rb").read())
    kind = lambda x: x[0] & 0x1F
    params = [x for x in nals if kind(x) in (7, 8)]       # SPS, PPS
    slices = [x for x in nals if kind(x) in (1, 5)]       # coded pictures
    if kind(slices[0]) != 5 or any(kind(x) != 1 for x in slices[1:]):
        raise RuntimeError("expected one keyframe followed by P-frames only")
    sc = b"\x00\x00\x00\x01"
    with open(dst, "wb") as f:
        for p in slices[1:]:
            for x in params + [slices[0], p]:
                f.write(sc + x)
    return len(slices) - 1


def packet_info(path):
    """Bytes stored per frame and whether it is a keyframe, in decode order
    (which is display order here, since there are no B-frames)."""
    out = run(["ffprobe", "-v", "error", "-show_entries", "packet=size,flags",
               "-of", "csv=p=0", path], capture_output=True, text=True).stdout
    sizes, types = [], []
    for line in out.splitlines():
        parts = line.strip().split(",")
        if parts and parts[0].isdigit():
            sizes.append(int(parts[0]))
            types.append("I" if len(parts) > 1 and "K" in parts[1] else "P")
    return sizes, types


def channel_change(path, w, h, fps):
    """Mean absolute change from the previous frame, per RGB channel, 0-100 %."""
    proc = subprocess.Popen(["ffmpeg", "-v", "error", "-framerate", f"{fps:.6f}",
                             "-i", path, "-fps_mode", "passthrough",
                             "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                            stdout=subprocess.PIPE)
    fb = w * h * 3
    rows, prev = [], None
    while True:
        buf = proc.stdout.read(fb)
        if len(buf) < fb:
            break
        cur = np.frombuffer(buf, np.uint8).reshape(h, w, 3).astype(np.int16)
        if prev is None:
            rows.append([0.0, 0.0, 0.0])
        else:
            d = np.abs(cur - prev).reshape(-1, 3).mean(axis=0) / 255.0 * 100.0
            rows.append(d.tolist())
        prev = cur
    proc.wait()
    return np.array(rows, dtype=np.float64)


def heat_tables():
    """Lookup tables: level from gray (0-255) -> heat index, index -> RGB colour."""
    dev = np.arange(256, dtype=np.float64)
    index = np.rint(255 * np.minimum(np.log1p(dev) / np.log1p(HEAT_MAX), 1)).astype(np.uint8)
    colours = (matplotlib.colormaps["inferno"](np.linspace(0, 1, 256))[:, :3] * 255)
    return index, np.rint(colours).astype(np.uint8)


def decode_rgb(path, w, h, fps, flags=()):
    """Start ffmpeg decoding a raw H.264 stream to RGB frames on a pipe."""
    return subprocess.Popen(["ffmpeg", "-v", "error", *flags, "-framerate", f"{fps:.6f}",
                             "-i", path, "-fps_mode", "passthrough",
                             "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                            stdout=subprocess.PIPE)


def stored_frames(enc, pairs, w, h, fps, needed, gain):
    """Yield, per frame of the clip, the piped panels side by side (in PIPED
    order, only those in `needed`) as RGB bytes, and the share of pixels the
    encoder copied. Each P-frame is measured against its own decoded gray
    keyframe, so rounding in the colour conversion cannot tint a panel.
      amp:  the frame's own data in colour, distance from gray times gain
      heat: levels from gray, log scale
      pred: decoded frame minus the frame's own data
      prev: the decoded frame before this one (the gray keyframe for frame 0)"""
    index, colours = heat_tables()
    fb = w * h * 3
    pair_proc = decode_rgb(pairs, w, h, fps, ["-flags2", "+showall", "-err_detect", "ignore_err"])
    dec_proc, prev = None, None
    if "pred" in needed or "prev" in needed:
        dec_proc = decode_rgb(enc, w, h, fps)
        prev = np.frombuffer(dec_proc.stdout.read(fb), np.uint8).reshape(h, w, 3)  # gray lead
    while True:
        gray = pair_proc.stdout.read(fb)
        frame = pair_proc.stdout.read(fb)
        if len(frame) < fb:
            break
        g = np.frombuffer(gray, np.uint8).reshape(h, w, 3).astype(np.int16)
        p = np.frombuffer(frame, np.uint8).reshape(h, w, 3).astype(np.int16)
        sent = p - g
        if dec_proc:
            d = dec_proc.stdout.read(fb)
            dec = np.frombuffer(d if len(d) == fb else bytes(fb), np.uint8).reshape(h, w, 3)
        dev = np.minimum(np.abs(sent).max(axis=2), 255).astype(np.uint8)
        copied = float((dev <= COPY_TOL).mean() * 100)
        parts = []
        for name in PIPED:
            if name not in needed:
                continue
            if name == "amp":
                parts.append(np.clip(sent * gain + 128, 0, 255).astype(np.uint8))
            elif name == "heat":
                parts.append(colours[index[dev]])
            elif name == "pred":
                parts.append(np.clip(dec.astype(np.int16) - sent, 0, 255).astype(np.uint8))
            else:
                parts.append(prev)
        if dec_proc:
            prev = dec
        yield np.ascontiguousarray(np.concatenate(parts, axis=1)).tobytes(), copied
    pair_proc.wait()
    if dec_proc:
        dec_proc.stdout.close()
        dec_proc.wait()


def draw_header(path, panel_w, labels):
    """One label band over a row of panels. Each label sits at the bottom of the
    band, next to its own panel; the heat-map key, where there is one, above it."""
    total_w = panel_w * len(labels)
    fig = plt.figure(figsize=(total_w / 100, HEADER_H / 100), dpi=100)
    fig.patch.set_facecolor(BG)
    for i, text in enumerate(labels):
        fig.text((i + 0.5) / len(labels), 0.08, text, ha="center", va="bottom",
                 color=FG, fontsize=22, family="sans-serif")
    heat = [i for i, text in enumerate(labels) if text.startswith("sent per pixel")]
    if heat:
        bar_w = 260 / total_w
        cx = (heat[0] + 0.5) / len(labels)
        ax = fig.add_axes([cx - bar_w / 2, 0.62, bar_w, 0.10])
        index, colours = heat_tables()
        ax.imshow(colours[np.newaxis, :, :], aspect="auto", extent=(0, 255, 0, 1))
        ax.set_yticks([])
        ax.set_xticks([index[v] for v in (0, 1, COPY_TOL, 16, HEAT_MAX)])
        ax.set_xticklabels(["0", "1", str(COPY_TOL), "16", f"{HEAT_MAX}+"], fontsize=9,
                           color=FG)
        ax.xaxis.tick_top()
        ax.tick_params(length=2, pad=1, colors=FG)
        for spine in ax.spines.values():
            spine.set_visible(False)
        fig.text(cx + bar_w / 2 + 6 / total_w, 0.67, "levels sent", ha="left",
                 va="center", color=FG, fontsize=9)
    fig.savefig(path, dpi=100, facecolor=BG)
    plt.close(fig)


def draw_timeline(path, total_w, times, kbytes, types, change):
    fig = plt.figure(figsize=(total_w / 100, TIMELINE_H / 100), dpi=100)
    fig.patch.set_facecolor(BG)
    left = AX_LEFT_PX / total_w
    width = (total_w - AX_LEFT_PX - AX_RIGHT_PX) / total_w
    ax1 = fig.add_axes([left, 0.52, width, 0.40])               # bytes stored
    ax2 = fig.add_axes([left, 0.17, width, 0.28], sharex=ax1)   # pixel change
    for ax in (ax1, ax2):
        ax.set_facecolor(BG)
        ax.tick_params(colors=FG, labelsize=11)
        for side in ("top", "right"):
            ax.spines[side].set_visible(False)
        for side in ("left", "bottom"):
            ax.spines[side].set_color("#555555")
    ax1.fill_between(times, kbytes, color=BYTES_COLOR, alpha=0.35, lw=0)
    ax1.plot(times, kbytes, color=BYTES_COLOR, lw=1.2)
    # Frame 0 has nothing to copy from, so it is drawn whole and is far larger
    # than the rest; scale to the others and label it instead of squashing them.
    rest = kbytes[1:] or kbytes
    ymax = max(rest) * 1.15
    ax1.set_ylim(0, ymax)
    if kbytes[0] > ymax:
        ax1.annotate(f"frame 0: {kbytes[0]:.0f} KB", xy=(times[0], ymax),
                     xytext=(8, -14), textcoords="offset points", color=BYTES_COLOR,
                     fontsize=11)
    ax1.set_ylabel("KB stored", color=FG, fontsize=11)
    plt.setp(ax1.get_xticklabels(), visible=False)
    lines = [ax2.plot(times, change[:, i], color=CHANNEL_COLORS[ch], lw=1.2,
                      label=ch)[0] for i, ch in enumerate("RGB")]
    ax2.set_ylim(bottom=0)
    ax2.set_ylabel("change %", color=FG, fontsize=11)
    ax2.set_xlabel("seconds", color=FG, fontsize=11)
    ax2.legend(handles=lines, loc="upper left", ncol=3, frameon=False,
               labelcolor=FG, fontsize=10)
    ax1.set_xlim(times[0], times[-1])
    fig.savefig(path, dpi=100, facecolor=BG)
    plt.close(fig)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("input", nargs="?")
    ap.add_argument("-o", "--output")
    ap.add_argument("--make-test", action="store_true",
                    help="generate framediff_test.mp4 (pattern + fractal) and process it")
    ap.add_argument("--crf", type=int, default=23,
                    help="H.264 quality, 0-51: higher sends less new data, so more of "
                         "the 'sent per pixel' panel stays black (default 23)")
    ap.add_argument("--view", choices=sorted(VIEWS), default="heat",
                    help="which panels: heat (default), amplified, both, prediction, "
                         "or all (both above prediction); see the top of this file")
    ap.add_argument("--gain", type=float, default=4,
                    help="for the amplified panel: how many times to boost the "
                         "distance from gray (default 4)")
    ap.add_argument("--min-panel-width", type=int, default=640,
                    help="small sources are scaled up so labels and timeline stay legible")
    args = ap.parse_args()

    if args.make_test:
        args.input = args.input or "framediff_test.mp4"
        make_test_clip(args.input)
    if not args.input:
        ap.error("give an input video, or use --make-test")
    src = args.input
    out = args.output or os.path.splitext(src)[0] + "_framediff.mp4"
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    csv_path = os.path.splitext(out)[0] + ".csv"

    w, h, fps = probe(src)
    # Panel size: half resolution, but at least --min-panel-width; even numbers
    pw = max(w // 2, args.min_panel_width) // 2 * 2
    ph = int(round(pw * h / w / 2)) * 2
    total_w = pw * 3

    with tempfile.TemporaryDirectory() as tmp:
        enc = os.path.join(tmp, "p_only.h264")
        pairs = os.path.join(tmp, "pairs.h264")
        print(f"encoding {pw}x{ph}, gray keyframe then P-frames, crf {args.crf}...",
              file=sys.stderr)
        encode_p_only(src, enc, pw, ph, fps, args.crf)
        pair_with_gray(enc, pairs)

        # Drop the gray lead frame everywhere: frame 0 is the clip's first frame
        sizes, types = packet_info(enc)
        sizes, types = sizes[1:], types[1:]
        print("measuring change per frame...", file=sys.stderr)
        change = channel_change(enc, pw, ph, fps)[1:]
        if len(change):
            change[0] = 0.0
        n = min(len(sizes), len(change))
        sizes, types, change = sizes[:n], types[:n], change[:n]
        times = [i / fps for i in range(n)]
        kbytes = [s / 1024 for s in sizes]

        rows = VIEWS[args.view]
        gain_label = f"{args.gain:g}"
        labels = [[label.format(gain=gain_label) for _, label in row] for row in rows]
        sources = [[name for name, _ in row] for row in rows]
        uses = {}
        for row in sources:
            for name in row:
                uses[name] = uses.get(name, 0) + 1
        needed = [name for name in PIPED if name in uses]
        n_rows = len(rows)
        row_h = HEADER_H + ph
        headers = [os.path.join(tmp, f"header{i}.png") for i in range(n_rows)]
        for path, row_labels in zip(headers, labels):
            draw_header(path, pw, row_labels)
        timeline_png = os.path.join(tmp, "timeline.png")
        draw_timeline(timeline_png, total_w, times, kbytes, types, change)

        duration = max(times[-1], 1e-6)
        plot_w = total_w - AX_LEFT_PX - AX_RIGHT_PX
        timing = f"settb=AVTB,setpts=N/({fps:.6f}*TB)"
        g = []   # filter graph lines
        # Input 0 has the gray lead frame first, so it is trimmed to the clip's
        # frames. Input 1 is the piped panels side by side, cut apart here. Both
        # get the same time base and frame-by-frame timestamps, so frame n of one
        # meets frame n of the other (left to their own clocks they drift by a
        # frame on a third of frames at 23.976 fps).
        decoded_outs = [x for x in ("dec", "mv") if x in uses]
        if decoded_outs:
            g.append(f"[0:v]trim=start_frame=1,{timing},format=yuv420p,"
                     f"split={len(decoded_outs)}" + "".join(f"[{x}_in]" for x in decoded_outs) + ";")
            if "dec" in uses:
                g.append("[dec_in]null[dec_src];")
            if "mv" in uses:
                g.append("[mv_in]codecview=mv=pf,format=yuv420p[mv_src];")
        else:
            g.append("[0:v]nullsink;")
        g.append(f"[1:v]{timing},split={len(needed)}" + "".join(f"[{x}_raw]" for x in needed) + ";")
        for i, name in enumerate(needed):
            g.append(f"[{name}_raw]crop={pw}:{ph}:{i * pw}:0,format=yuv420p[{name}_src];")
        for name, count in uses.items():   # a panel can appear in more than one row
            g.append(f"[{name}_src]split={count}" + "".join(f"[{name}{k}]" for k in range(count)) + ";")
        taken = {name: 0 for name in uses}
        for r, row in enumerate(sources):
            ins = ""
            for name in row:
                ins += f"[{name}{taken[name]}]"
                taken[name] += 1
            g.append(f"{ins}hstack=inputs=3,pad={total_w}:{row_h}:0:{HEADER_H}:black[row{r}];")
        body = "".join(f"[row{r}]" for r in range(n_rows))
        height = n_rows * row_h + TIMELINE_H
        if n_rows > 1:
            g.append(f"{body}vstack=inputs={n_rows},pad={total_w}:{height}:0:0:black[c0];")
        else:
            g.append(f"[row0]pad={total_w}:{height}:0:0:black[c0];")
        # Labels, timeline and playhead are still images laid on the canvas; the
        # playhead (one white frame, held) is placed from each frame's timestamp,
        # so nothing else keeps time with the video and no frame is repeated.
        k = 0
        for r in range(n_rows):
            g.append(f"[{2 + r}:v]format=yuva420p[h{r}];[c{k}][h{r}]overlay=0:{r * row_h}:"
                     f"eof_action=repeat[c{k + 1}];")
            k += 1
        tl_input = 2 + n_rows
        tl_y = n_rows * row_h
        g.append(f"[{tl_input}:v]format=yuva420p[tl];[c{k}][tl]overlay=0:{tl_y}:eof_action=repeat[c{k + 1}];")
        k += 1
        g.append(f"color=c=white:s=3x{TIMELINE_H}:r={fps:.6f}:d={1 / fps:.6f},format=yuva420p[ph];")
        g.append(f"[c{k}][ph]overlay=x='{AX_LEFT_PX}+min(t/{duration:.6f}\\,1)*{plot_w}':"
                 f"y={tl_y}:eval=frame:eof_action=repeat"
                 ",format=yuv420p[out]")
        fc = "\n".join(g)

        rate = f"{fps:.6f}"
        cmd = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-stats",
               "-flags2", "+export_mvs", "-framerate", rate, "-i", enc,
               "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{pw * len(needed)}x{ph}",
               "-framerate", rate, "-i", "pipe:0"]
        for path in headers:
            cmd += ["-i", path]
        cmd += ["-i", timeline_png, "-i", src,
                "-filter_complex", fc, "-map", "[out]", "-map", f"{tl_input + 1}:a?",
                "-r", rate, "-c:v", "libx264", "-crf", "18", "-c:a", "aac",
                "-shortest", out]
        print("rendering...", file=sys.stderr)
        proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
        copied = []
        try:
            for panels, share in stored_frames(enc, pairs, pw, ph, fps, needed, args.gain):
                if len(copied) >= n:
                    break
                proc.stdin.write(panels)
                copied.append(share)
        except BrokenPipeError:
            pass
        finally:
            try:
                proc.stdin.close()
            except BrokenPipeError:
                pass
        if proc.wait() != 0:
            raise SystemExit("ffmpeg failed while rendering; see the error above")
        copied += [float("nan")] * (n - len(copied))

    with open(csv_path, "w", newline="") as f:
        wr = csv.writer(f)
        wr.writerow(["frame", "time_s", "type", "bytes", "copied_pct",
                     "R_change_pct", "G_change_pct", "B_change_pct"])
        for i in range(n):
            wr.writerow([i, f"{times[i]:.4f}", types[i], sizes[i], f"{copied[i]:.2f}"]
                        + [f"{v:.4f}" for v in change[i]])
    layout_path = os.path.splitext(out)[0] + ".json"
    with open(layout_path, "w") as f:
        json.dump({"view": args.view, "gain": args.gain, "crf": args.crf,
                   "panel_w": pw, "panel_h": ph, "header_h": HEADER_H,
                   "timeline_h": TIMELINE_H, "sources": sources, "labels": labels}, f, indent=1)
    print(f"wrote {out}\nwrote {csv_path}\nwrote {layout_path}", file=sys.stderr)


if __name__ == "__main__":
    main()
