#!/usr/bin/env python3
"""
framediff.py: build a labeled three-panel video (original / changed / unchanged)
with a per-channel change timeline and a moving playhead underneath.

Usage:
    python3 framediff.py input.mp4
    python3 framediff.py input.mov -o out.mp4 --threshold 12
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

HEADER_H = 64          # label bar above the panels, in pixels
TIMELINE_H = 320       # timeline strip below the panels, in pixels
AX_LEFT_PX = 90        # timeline plot margins, in pixels (fixed so the
AX_RIGHT_PX = 40       # playhead lines up with the plotted data)
BG = "#000000"
FG = "#d8d8d8"
CHANNEL_COLORS = {"R": "#ff4d4d", "G": "#3ddc84", "B": "#4d8dff", "A": "#bbbbbb"}


def run(cmd, **kw):
    return subprocess.run(cmd, check=True, **kw)


def probe(path):
    out = run(["ffprobe", "-v", "error", "-select_streams", "v:0",
               "-show_entries", "stream=width,height,pix_fmt,avg_frame_rate",
               "-of", "json", path], capture_output=True).stdout
    s = json.loads(out)["streams"][0]
    num, den = s["avg_frame_rate"].split("/")
    fps = float(num) / float(den) if float(den) else 30.0
    return int(s["width"]), int(s["height"]), s["pix_fmt"], fps


def probe_frames(path):
    """Per-frame timestamp and picture type (I/P/B) as the decoder reports them."""
    out = run(["ffprobe", "-v", "error", "-select_streams", "v:0",
               "-show_entries", "frame=best_effort_timestamp_time,pict_type",
               "-of", "csv=p=0", path], capture_output=True, text=True).stdout
    times, types = [], []
    for line in out.splitlines():
        parts = [p for p in line.strip().split(",") if p]
        t = next((p for p in parts if p.replace(".", "", 1).isdigit()), None)
        pt = next((p for p in parts if p in ("I", "P", "B", "?")), "?")
        if t is not None:
            times.append(float(t))
            types.append(pt)
    return times, types


def make_test_clip(path):
    """7 s test clip: 4 s of moving test pattern, a hard cut, 3 s of zooming
    Mandelbrot fractal. The cut forces an I-frame and a spike on the timeline."""
    run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
         "-f", "lavfi", "-i", "testsrc2=s=1280x720:r=30:d=4",
         "-f", "lavfi", "-i", "mandelbrot=s=1280x720:r=30,trim=duration=3",
         "-f", "lavfi", "-i", "sine=d=7",
         "-filter_complex", "[0:v][1:v]concat=n=2:v=1[v]",
         "-map", "[v]", "-map", "2:a", "-c:v", "libx264", "-pix_fmt", "yuv420p",
         "-c:a", "aac", path])
    print(f"made test clip {path}", file=sys.stderr)


def has_alpha(pix_fmt):
    return pix_fmt.startswith(("yuva", "rgba", "bgra", "argb", "abgr", "gbrap", "ya"))


def compute_metrics(path, w, h, alpha, threshold):
    """Mean absolute change per channel (0-100 %) and % of pixels over threshold."""
    fmt, nch = ("rgba", 4) if alpha else ("rgb24", 3)
    frame_bytes = w * h * nch
    proc = subprocess.Popen(["ffmpeg", "-v", "error", "-i", path, "-map", "0:v:0",
                             "-f", "rawvideo", "-pix_fmt", fmt, "-"],
                            stdout=subprocess.PIPE)
    luma_w = np.array([0.299, 0.587, 0.114], dtype=np.float32)
    rows, prev, n = [], None, 0
    while True:
        buf = proc.stdout.read(frame_bytes)
        if len(buf) < frame_bytes:
            break
        cur = np.frombuffer(buf, np.uint8).reshape(h, w, nch).astype(np.int16)
        if prev is None:
            rows.append([0.0] * nch + [0.0])
        else:
            d = np.abs(cur - prev)
            per_ch = (d.reshape(-1, nch).mean(axis=0) / 255.0 * 100.0).tolist()
            # Same rule as the video's mask: luma of the RGB difference > threshold
            luma = d[..., :3].astype(np.float32) @ luma_w
            changed_pct = float((luma > threshold).mean() * 100.0)
            rows.append(per_ch + [changed_pct])
        prev = cur
        n += 1
        if n % 100 == 0:
            print(f"  analyzed {n} frames", file=sys.stderr)
    proc.wait()
    return np.array(rows, dtype=np.float64)


def draw_header(path, panel_w, labels):
    total_w = panel_w * len(labels)
    fig = plt.figure(figsize=(total_w / 100, HEADER_H / 100), dpi=100)
    fig.patch.set_facecolor(BG)
    for i, text in enumerate(labels):
        fig.text((i + 0.5) / len(labels), 0.5, text, ha="center", va="center",
                 color=FG, fontsize=22, family="sans-serif")
    fig.savefig(path, dpi=100, facecolor=BG)
    plt.close(fig)


def draw_timeline(path, total_w, times, metrics, types, channels, threshold):
    fig = plt.figure(figsize=(total_w / 100, TIMELINE_H / 100), dpi=100)
    fig.patch.set_facecolor(BG)
    left = AX_LEFT_PX / total_w
    width = (total_w - AX_LEFT_PX - AX_RIGHT_PX) / total_w
    ax1 = fig.add_axes([left, 0.46, width, 0.48])   # per-channel change
    ax2 = fig.add_axes([left, 0.17, width, 0.20], sharex=ax1)  # % pixels changed
    t0, t1 = times[0], times[-1]
    for ax in (ax1, ax2):
        ax.set_facecolor(BG)
        ax.tick_params(colors=FG, labelsize=11)
        for side in ("top", "right"):
            ax.spines[side].set_visible(False)
        for side in ("left", "bottom"):
            ax.spines[side].set_color("#555555")
        # Mark the encoder's I-frames: full images, where prediction restarts
        for t, pt in zip(times, types):
            if pt == "I":
                ax.axvline(t, color="#ffcc33", lw=1, alpha=0.6, ls="--")
    lines = [ax1.plot(times, metrics[:, i], color=CHANNEL_COLORS[ch], lw=1.4,
                      label=ch)[0] for i, ch in enumerate(channels)]
    ax1.set_ylabel("mean change %", color=FG, fontsize=11)
    ax1.set_ylim(bottom=0)
    ax1.legend(loc="upper left", ncol=len(channels) + 1, frameon=False,
               labelcolor=FG, fontsize=11,
               handles=lines + [plt.Line2D([], [], color="#ffcc33",
                                                     ls="--", label="I-frame")])
    plt.setp(ax1.get_xticklabels(), visible=False)
    ax2.fill_between(times, metrics[:, -1], color="#888888", lw=0)
    ax2.set_ylim(0, 100)
    ax2.set_yticks([0, 50, 100])
    ax2.set_ylabel("% px changed", color=FG, fontsize=11)
    ax2.set_xlabel("seconds", color=FG, fontsize=11)
    ax1.set_xlim(t0, t1)
    fig.savefig(path, dpi=100, facecolor=BG)
    plt.close(fig)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("input", nargs="?")
    ap.add_argument("--make-test", action="store_true",
                    help="generate framediff_test.mp4 (pattern + fractal) and process it")
    ap.add_argument("-o", "--output")
    ap.add_argument("--threshold", type=float, default=8,
                    help="change needed for a pixel to count as changed (0-255)")
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
    w, h, pix_fmt, fps = probe(src)
    alpha = has_alpha(pix_fmt)
    channels = ["R", "G", "B"] + (["A"] if alpha else [])
    print(f"{w}x{h} {pix_fmt} {fps:.3f} fps, channels: {''.join(channels)}",
          file=sys.stderr)

    print("reading frame types...", file=sys.stderr)
    times, types = probe_frames(src)
    print("measuring change per frame...", file=sys.stderr)
    metrics = compute_metrics(src, w, h, alpha, args.threshold)
    n = min(len(times), len(metrics))
    if len(times) < len(metrics):  # fall back to constant frame rate
        times = [i / fps for i in range(len(metrics))]
        types = types + ["?"] * (len(metrics) - len(types))
        n = len(metrics)
    t0 = times[0]
    times = [t - t0 for t in times[:n]]
    types, metrics = types[:n], metrics[:n]

    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    csv_path = os.path.splitext(out)[0] + ".csv"
    with open(csv_path, "w", newline="") as f:
        wr = csv.writer(f)
        wr.writerow(["frame", "time_s", "type"] + [f"{c}_change_pct" for c in channels]
                    + ["pixels_changed_pct"])
        for i in range(n):
            wr.writerow([i, f"{times[i]:.4f}", types[i]]
                        + [f"{v:.4f}" for v in metrics[i]])

    # Panel size: half resolution, but at least --min-panel-width; even numbers
    pw = max(w // 2, args.min_panel_width) // 2 * 2
    ph = int(round(pw * h / w / 2)) * 2
    total_w = pw * 3
    tmpdir = tempfile.TemporaryDirectory()
    tmp = tmpdir.name
    header_png = os.path.join(tmp, "header.png")
    timeline_png = os.path.join(tmp, "timeline.png")
    draw_header(header_png, pw, ["original", "changed", "unchanged"])
    draw_timeline(timeline_png, total_w, times, metrics, types, channels, args.threshold)

    duration = max(times[-1], 1e-6)
    plot_w = total_w - AX_LEFT_PX - AX_RIGHT_PX
    thr = args.threshold
    fc = f"""
[0:v]scale={pw}:{ph},format=gbrp,split=5[a][b][c][d][e];
[b]tblend=all_mode=difference,format=gray,split=2[d1][d2];
[d1]lut=c0='if(gt(val,{thr}),255,0)',format=gbrp[mask];
[d2]lut=c0='if(gt(val,{thr}),0,255)',format=gbrp[inv];
[c]lutrgb=r=0:g=0:b=0,split=2[k1][k2];
[k1][d][mask]maskedmerge[changed];
[k2][e][inv]maskedmerge[unchanged];
[a][changed][unchanged]hstack=inputs=3,format=yuv420p[panels];
[1:v]format=yuv420p[hdr];
[2:v]format=yuv420p[tl];
[hdr][panels][tl]vstack=inputs=3:shortest=1[stack];
color=c=white:s=3x{TIMELINE_H}:r={fps:.6f}[ph];
[stack][ph]overlay=x='{AX_LEFT_PX}+min(t/{duration:.6f},1)*{plot_w}':y={HEADER_H + ph}:shortest=1,format=yuv420p[out]
"""
    cmd = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-stats",
           "-i", src,
           "-loop", "1", "-framerate", f"{fps:.6f}", "-i", header_png,
           "-loop", "1", "-framerate", f"{fps:.6f}", "-i", timeline_png,
           "-filter_complex", fc, "-map", "[out]", "-map", "0:a?",
           "-r", f"{fps:.6f}", "-c:v", "libx264", "-crf", "18", "-c:a", "aac",
           "-shortest", out]
    run(cmd)
    tmpdir.cleanup()
    print(f"wrote {out}\nwrote {csv_path}", file=sys.stderr)


if __name__ == "__main__":
    main()
