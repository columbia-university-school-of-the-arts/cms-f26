"""Timing, scoring and FFmpeg evidence utilities, independent of the interface."""
import hashlib
import json
import math
from pathlib import Path
import subprocess

import cv2


def command(args):
    result = subprocess.run(args, capture_output=True, text=True, timeout=300)
    if result.returncode:
        raise RuntimeError(result.stderr[-4000:] or f"Command failed: {args[0]}")
    return result.stdout


def fingerprint(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as source:
        for block in iter(lambda: source.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def source_url(path):
    """The page a yt-dlp download came from, read from its sibling .info.json."""
    info = Path(path).with_suffix('.info.json')
    try:
        data = json.loads(info.read_text())
    except (OSError, ValueError):
        return ''
    return data.get('webpage_url') or data.get('original_url') or ''


def timing(path):
    data = json.loads(command([
        'ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_frames',
        '-show_entries', 'frame=best_effort_timestamp_time,duration_time,pkt_duration_time',
        '-of', 'json', str(path)]))
    frames = data.get('frames', [])
    if len(frames) < 2:
        raise ValueError('At least two timestamped video frames are needed.')
    times = [float(f['best_effort_timestamp_time']) for f in frames]
    origin = times[0]
    times = [t - origin for t in times]
    if not all(math.isfinite(t) for t in times) or any(b <= a for a, b in zip(times, times[1:])):
        raise ValueError('Frame timestamps must be finite and strictly increasing.')
    last = frames[-1]
    tail = float(last.get('duration_time') or last.get('pkt_duration_time') or 0)
    estimated_tail = tail <= 0
    if estimated_tail:
        tail = times[-1] - times[-2]
    return {'times': times, 'duration': times[-1] + tail,
            'source_origin': origin, 'estimated_last_frame_duration': estimated_tail}


def analyze(path, width, parameters, score_pair):
    clock = timing(path)
    cap = cv2.VideoCapture(str(path))
    if not cap.isOpened():
        raise ValueError('OpenCV could not open this video.')
    previous = None
    scores = []
    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                break
            h, w = frame.shape[:2]
            target = w if width == 'native' else min(width, w)
            frame = cv2.resize(frame, (target, max(1, round(h * target / w))), interpolation=cv2.INTER_AREA)
            score = 0.0 if previous is None else float(score_pair(previous, frame, parameters))
            if not math.isfinite(score):
                raise ValueError(f'Non-finite score at frame {len(scores)}.')
            scores.append(score)
            previous = frame
    finally:
        cap.release()
    if len(scores) != len(clock['times']):
        raise ValueError('ffprobe/OpenCV frame counts differ; do not use these timestamps. Ask Claude to investigate the source encoding.')
    return {**clock, 'scores': scores, 'frame_count': len(scores)}


def boundaries(times, scores, threshold, minimum_gap):
    """Keep the first above-threshold boundary, then enforce a gap in seconds."""
    cuts = []
    last = 0.0
    for t, score in zip(times[1:], scores[1:]):
        if score > threshold and t - last >= minimum_gap:
            cuts.append(t)
            last = t
    return cuts


def shot_table(cuts, duration):
    if not math.isfinite(duration) or duration <= 0:
        raise ValueError('Duration must be positive and finite.')
    if any(not math.isfinite(c) or c <= 0 or c >= duration for c in cuts):
        raise ValueError('Cuts must be strictly inside the video interval.')
    points = [0.0, *sorted(set(cuts)), duration]
    return [{'shot': i + 1, 'start_s': a, 'end_s': b, 'length_s': b - a}
            for i, (a, b) in enumerate(zip(points, points[1:]))]


def export_clip(source, start, end, target):
    if not (math.isfinite(start) and math.isfinite(end) and 0 <= start < end):
        raise ValueError('Clip interval must have positive length.')
    target = Path(target)
    target.parent.mkdir(parents=True, exist_ok=True)
    # Output seeking decodes before trimming. Re-encode, never keyframe stream-copy.
    # Local classroom exports omit audio so video timing defines the duration.
    command(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', '-i', str(source),
             '-ss', f'{start:.9f}', '-t', f'{end - start:.9f}', '-map', '0:v:0',
             '-an', '-c:v', 'libx264', '-preset', 'fast', '-crf', '20',
             '-vf', 'pad=ceil(iw/2)*2:ceil(ih/2)*2', '-pix_fmt', 'yuv420p',
             '-fps_mode', 'vfr', '-movflags', '+faststart', str(target)])
    return target


def boundary_frames(source, frame_index):
    """Read adjacent decoded frames for human inspection; convert BGR to RGB."""
    cap = cv2.VideoCapture(str(source))
    try:
        cap.set(cv2.CAP_PROP_POS_FRAMES, max(0, frame_index - 1))
        ok_a, before = cap.read()
        ok_b, after = cap.read()
        if not (ok_a and ok_b):
            raise ValueError('Could not decode the selected frame pair.')
        return cv2.cvtColor(before, cv2.COLOR_BGR2RGB), cv2.cvtColor(after, cv2.COLOR_BGR2RGB)
    finally:
        cap.release()
