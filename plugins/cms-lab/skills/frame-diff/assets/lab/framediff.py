#!/usr/bin/env python3
"""
framediff.py: show what a video encoder actually stores, frame by frame.

The script re-encodes the clip with H.264 as a flat gray keyframe followed
only by P-frames (every frame of the clip becomes a P-frame), then renders
three labeled panels over a timeline:

  decoded video           the encode, as a viewer sees it
  sent per pixel          every P-frame decoded on its own, against the gray
                          keyframe instead of the frame before it, then drawn
                          as a heat map: black where the encoder only copied,
                          brighter the more it sent (corrections, and blocks
                          drawn from scratch), on a log scale so that small
                          corrections show
  motion vectors          the encoder's own arrows: "copy this block from there"

Timeline: bytes the encoder stored for each frame, and the mean change in
each colour channel, with a playhead that follows the video.

Usage:
    python3 framediff.py input.mp4
    python3 framediff.py input.mov -o out.mp4 --crf 30
    python3 framediff.py --make-test            # builds and processes a test clip

Needs ffmpeg + ffprobe on PATH, and: pip install numpy matplotlib
Also writes <output>.csv with the per-frame numbers.
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
VIEWS = {   # --view: the three panels, left to right
    "heat": ["decoded video", "sent per pixel", "motion vectors"],
    "amplified": ["decoded video", "sent, amplified", "motion vectors"],
    "both": ["decoded + motion vectors", "sent, amplified", "sent per pixel"],
}
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


def stored_frames(pairs, w, h, fps, view, gain):
    """Decode the (gray keyframe, P-frame) pairs and yield, per P-frame, the
    piped panel(s) as RGB bytes and the share of pixels the encoder copied.
    Each P-frame is measured against its own decoded gray keyframe, so
    rounding in the colour conversion cannot tint the panel.
    heat: brightness = levels from gray, log scale. amplified: the frame's own
    data in colour, its distance from gray multiplied by --gain."""
    index, colours = heat_tables()
    proc = subprocess.Popen(["ffmpeg", "-v", "error", "-flags2", "+showall",
                             "-err_detect", "ignore_err", "-framerate", f"{fps:.6f}",
                             "-i", pairs, "-fps_mode", "passthrough",
                             "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                            stdout=subprocess.PIPE)
    fb = w * h * 3
    while True:
        gray = proc.stdout.read(fb)
        frame = proc.stdout.read(fb)
        if len(frame) < fb:
            break
        g = np.frombuffer(gray, np.uint8).reshape(h, w, 3).astype(np.int16)
        p = np.frombuffer(frame, np.uint8).reshape(h, w, 3).astype(np.int16)
        dev = np.minimum(np.abs(p - g).max(axis=2), 255).astype(np.uint8)
        copied = float((dev <= COPY_TOL).mean() * 100)
        heat = colours[index[dev]]
        amp = np.clip((p - g) * gain + 128, 0, 255).astype(np.uint8)
        if view == "heat":
            out = heat
        elif view == "amplified":
            out = amp
        else:
            out = np.concatenate([amp, heat], axis=1)
        yield np.ascontiguousarray(out).tobytes(), copied
    proc.wait()


def draw_header(path, panel_w, labels, heat_at, gain):
    total_w = panel_w * len(labels)
    fig = plt.figure(figsize=(total_w / 100, HEADER_H / 100), dpi=100)
    fig.patch.set_facecolor(BG)
    for i, text in enumerate(labels):
        if text == "sent, amplified":
            text = f"sent, amplified {gain:g}x"
        fig.text((i + 0.5) / len(labels), 0.68, text, ha="center", va="center",
                 color=FG, fontsize=22, family="sans-serif")
    if heat_at is None:
        fig.savefig(path, dpi=100, facecolor=BG)
        plt.close(fig)
        return
    # A key for the heat map under its label: the scale is levels from gray
    bar_w = 260 / total_w
    cx = (heat_at + 0.5) / len(labels)
    ax = fig.add_axes([cx - bar_w / 2, 0.24, bar_w, 0.10])
    index, colours = heat_tables()
    ax.imshow(colours[np.newaxis, :, :], aspect="auto", extent=(0, 255, 0, 1))
    ax.set_yticks([])
    ax.set_xticks([index[v] for v in (0, 1, COPY_TOL, 16, HEAT_MAX)])
    ax.set_xticklabels(["0", "1", str(COPY_TOL), "16", f"{HEAT_MAX}+"], fontsize=9, color=FG)
    ax.tick_params(length=2, pad=1, colors=FG)
    for spine in ax.spines.values():
        spine.set_visible(False)
    fig.text(cx + bar_w / 2 + 6 / total_w, 0.29, "levels sent", ha="left",
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
                    help="heat: heat map of what each frame sent (default); amplified: "
                         "what each frame sent, in colour, boosted by --gain; both: "
                         "motion vectors on the decoded video, then amplified, then heat")
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

        header_png = os.path.join(tmp, "header.png")
        timeline_png = os.path.join(tmp, "timeline.png")
        labels = VIEWS[args.view]
        heat_at = labels.index("sent per pixel") if "sent per pixel" in labels else None
        draw_header(header_png, pw, labels, heat_at, args.gain)
        draw_timeline(timeline_png, total_w, times, kbytes, types, change)

        duration = max(times[-1], 1e-6)
        plot_w = total_w - AX_LEFT_PX - AX_RIGHT_PX
        # The header and timeline are single still images laid onto a padded
        # canvas, and the playhead (a one-frame white line, held) is placed from each
        # frame's own timestamp, so
        # nothing else has to keep time with the video and no frame is repeated.
        # Input 0 has the gray lead frame first, so it is trimmed to the clip's
        # frames. Input 1 is the stored-data panel(s), piped in. Both get the
        # same time base and frame-by-frame timestamps, so that frame n of each
        # meets frame n of the other (left to their own clocks, the two drift
        # by one frame on a third of frames at 23.976 fps).
        fc = f"""
[0:v]trim=start_frame=1,settb=AVTB,setpts=N/({fps:.6f}*TB),format=yuv420p,split=2[a][m];
[m]codecview=mv=pf,format=yuv420p[mv];
[1:v]settb=AVTB,setpts=N/({fps:.6f}*TB),format=yuv420p[b];
{"[a][b][mv]hstack=inputs=3[panels];" if args.view != "both" else "[a]nullsink;[mv][b]hstack=inputs=2[panels];"}
[2:v]format=yuv420p[hdr];
[3:v]format=yuv420p[tl];
[panels]pad={total_w}:{HEADER_H + ph + TIMELINE_H}:0:{HEADER_H}:black[canvas];
[canvas][hdr]overlay=0:0:eof_action=repeat[c1];
[c1][tl]overlay=0:{HEADER_H + ph}:eof_action=repeat[c2];
color=c=white:s=3x{TIMELINE_H}:r={fps:.6f}:d={1 / fps:.6f},format=yuva420p[ph];
[c2][ph]overlay=x='{AX_LEFT_PX}+min(t/{duration:.6f}\\,1)*{plot_w}':y={HEADER_H + ph}:eval=frame:eof_action=repeat,format=yuv420p[out]
"""
        rate = f"{fps:.6f}"
        cmd = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-stats",
               "-flags2", "+export_mvs", "-framerate", rate, "-i", enc,
               "-f", "rawvideo", "-pix_fmt", "rgb24",
               "-s", f"{pw * (2 if args.view == 'both' else 1)}x{ph}",
               "-framerate", rate, "-i", "pipe:0",
               "-i", header_png,
               "-i", timeline_png,
               "-i", src,
               "-filter_complex", fc, "-map", "[out]", "-map", "4:a?",
               "-r", rate, "-c:v", "libx264", "-crf", "18", "-c:a", "aac",
               "-shortest", out]
        print("rendering...", file=sys.stderr)
        proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
        copied = []
        try:
            for heat, share in stored_frames(pairs, pw, ph, fps, args.view, args.gain):
                if len(copied) >= n:
                    break
                proc.stdin.write(heat)
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
    print(f"wrote {out}\nwrote {csv_path}", file=sys.stderr)


if __name__ == "__main__":
    main()
