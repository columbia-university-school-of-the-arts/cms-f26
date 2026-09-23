"""Run from the copied lab: python -m streamlit run app.py."""
import csv
import bisect
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import json
from pathlib import Path
import platform
import subprocess

import streamlit as st
import detector
from lab import analyze, boundary_frames, boundaries, command, export_clip, fingerprint, shot_table

ROOT = Path(__file__).resolve().parent
MEDIA = ROOT / 'media'
MEDIA.mkdir(exist_ok=True)
st.set_page_config(page_title='A cut is a decision', layout='wide')
st.title('A cut is a decision')
st.caption('Invent a rule. Make its decisions visible. Check what it missed.')

with st.expander('Choose a video', expanded=True):
    st.write('Download the workshop clip with yt-dlp first, then select the file or upload your own local video.')
    uploaded = st.file_uploader('Local video', type=['mp4', 'mkv', 'webm', 'mov'])
    if uploaded is not None:
        payload = uploaded.getvalue()
        target = MEDIA / (hashlib.sha256(payload).hexdigest()[:16] + Path(uploaded.name).suffix.lower())
        if not target.exists():
            target.write_bytes(payload)
    files = sorted(p for p in MEDIA.iterdir() if p.suffix.lower() in {'.mp4', '.mkv', '.webm', '.mov'})
    if not files:
        st.info('Your downloaded video goes in this lab’s media folder. No video is bundled with the course plugin.')
        st.stop()
    source = st.selectbox('Video in media/', files, format_func=lambda p: p.name)
    source_url = st.text_input('Source URL or description', value='https://www.youtube.com/watch?v=-1tza4BxVfA')
    st.caption('Confirm the source description matches the file you selected. It is saved as your attribution.')

st.subheader('Watch before measuring')
st.video(str(source))
st.caption('If this container will not play in your browser, ask Claude to make an H.264 MP4 viewing copy with FFmpeg. Keep the analyzed source identified.')
manual = st.text_area('Manual cuts in seconds, separated by commas', help='Mark these before inspecting the detector. Keep uncertain observations in your notes.')
observations = st.text_area('Your rule, observations and uncertainty', help='Record missed cuts and false alarms with timestamps. These notes travel with the saved run.')

st.sidebar.header(detector.NAME)
st.sidebar.write(detector.DESCRIPTION)
width = st.sidebar.select_slider('Analysis width (pixels)', options=[160, 320, 480, 640, 'native'], value=320,
                                  help='Every frame is analyzed; smaller images change the measurement and use less time.')
parameters = {}
for name, spec in detector.PARAMETERS.items():
    parameters[name] = st.sidebar.slider(name, spec['min'], spec['max'], spec['default'], spec['step'], help=spec['help'])
spec = detector.THRESHOLD
threshold = st.sidebar.slider('Cut threshold', spec['min'], spec['max'], spec['default'], spec['step'], help=spec['help'])
gap = st.sidebar.slider('Minimum gap (seconds)', 0.0, 2.0, 0.2, 0.05,
                        help='Keep the first qualifying boundary, then suppress nearby ones. This can hide real short shots.')

@st.cache_data(show_spinner=False)
def score_video(path, file_hash, analysis_width, params, detector_source):
    return analyze(path, analysis_width, params, detector.score_pair)

try:
    source_hash = fingerprint(source)
    code = (ROOT / 'detector.py').read_text()
    with st.spinner('Measuring frame changes…'):
        result = score_video(str(source), source_hash, width, parameters, code)
except NotImplementedError as error:
    st.info(str(error))
    st.stop()
except (ValueError, RuntimeError, OSError, KeyError, subprocess.TimeoutExpired) as error:
    st.error(str(error))
    st.stop()

cuts = boundaries(result['times'], result['scores'], threshold, gap)
shots = shot_table(cuts, result['duration'])
manual_error = None
try:
    marked = sorted(set(float(t.strip()) for t in manual.split(',') if t.strip()))
    shot_table(marked, result['duration'])  # validate finite interior marks
except ValueError as error:
    marked = []
    manual_error = str(error)
    st.warning(f'Fix manual timestamps before saving: {error}')

left, middle, right = st.columns(3)
left.metric('Proposed cuts', len(cuts))
middle.metric('Shots in this excerpt', len(shots))
right.metric('Average shot length', f"{result['duration'] / len(shots):.3f} s")
st.write(f"Shortest shot: {min(s['length_s'] for s in shots):.3f}s · Longest shot: {max(s['length_s'] for s in shots):.3f}s")
st.caption('Average = analyzed video duration ÷ shots. First and last shots may be partial. Proposed cuts are not verified cuts.')

# Vega-Lite layers put evidence and decisions on the same clock.
plot_rows = [{'time': t, 'score': s} for t, s in zip(result['times'], result['scores'])]
st.vega_lite_chart({'layer': [
    {'data': {'values': plot_rows}, 'mark': 'line', 'encoding': {
        'x': {'field': 'time', 'type': 'quantitative', 'title': 'Time (seconds)'},
        'y': {'field': 'score', 'type': 'quantitative', 'title': 'Change score'}}},
    {'data': {'values': [{'threshold': threshold}]}, 'mark': {'type': 'rule', 'color': '#dd7a00'},
     'encoding': {'y': {'field': 'threshold', 'type': 'quantitative'}}},
    {'data': {'values': [{'time': t} for t in cuts]}, 'mark': {'type': 'rule', 'color': '#d33', 'opacity': 0.6},
     'encoding': {'x': {'field': 'time', 'type': 'quantitative'}}},
    {'data': {'values': [{'time': t} for t in marked]}, 'mark': {'type': 'rule', 'color': '#19845b', 'strokeDash': [4, 4]},
     'encoding': {'x': {'field': 'time', 'type': 'quantitative'}}}
]}, width='stretch')
st.caption('Blue: change score · orange: threshold · red: proposed cuts · green dashed: manual marks')
st.dataframe(shots, hide_index=True, width='stretch')

st.subheader('Inspect the actual footage')
st.write('Render any shot, or a short window around a proposed or manually marked boundary. Watch the whole video too: a missed cut may be inside a long predicted shot.')
choice = st.selectbox('Shot to inspect', list(range(len(shots))), format_func=lambda i: f"Shot {i + 1}: {shots[i]['start_s']:.3f}–{shots[i]['end_s']:.3f}s")
clip_root = ROOT / 'clips' / source_hash[:16]

def show_clip(start, end, label):
    name = hashlib.sha256(f'{start:.9f}:{end:.9f}'.encode()).hexdigest()[:16] + '.mp4'
    target = clip_root / name
    try:
        if not target.exists():
            with st.spinner('FFmpeg is rendering this interval…'):
                export_clip(source, start, end, target)
        st.caption(f'{label}: {start:.3f}–{end:.3f}s · silent H.264 preview')
        st.video(str(target))
    except (ValueError, RuntimeError, OSError, subprocess.TimeoutExpired) as error:
        if target.exists():
            target.unlink()  # failed renders must not become cached evidence
        st.error(str(error))

if st.checkbox('Show selected shot'):
    show_clip(shots[choice]['start_s'], shots[choice]['end_s'], 'Selected shot')
inspect_times = sorted(set(cuts + marked))
if inspect_times:
    boundary = st.selectbox('Boundary to inspect (seconds)', inspect_times)
    if st.checkbox('Show frames on either side'):
        index = min(len(result['times']) - 1, max(1, bisect.bisect_left(result['times'], boundary)))
        try:
            before, after = boundary_frames(source, index)
            if hasattr(detector, 'inspect_frame'):
                before = detector.inspect_frame(before, parameters)
                after = detector.inspect_frame(after, parameters)
            a, b = st.columns(2)
            a.image(before, caption=f"Frame {index - 1} · {result['times'][index - 1]:.3f}s")
            b.image(after, caption=f"Frame {index} · {result['times'][index]:.3f}s")
        except ValueError as error:
            st.error(str(error))
    padding = st.slider('Seconds on each side', 0.1, 2.0, 0.5, 0.1)
    if st.checkbox('Show boundary preview'):
        show_clip(max(0, boundary - padding), min(result['duration'], boundary + padding), 'Across boundary')

st.subheader('Save an experiment')
label = st.text_input('Run label', value='invented-rule-01')
if st.button('Save run and shot table', disabled=manual_error is not None):
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S.%fZ')
    folder = ROOT / 'runs' / stamp
    folder.mkdir(parents=True, exist_ok=False)
    versions = {name: importlib.metadata.version(name) for name in ['streamlit', 'numpy', 'opencv-python-headless', 'yt-dlp']}
    versions['python'] = platform.python_version()
    versions['ffmpeg'] = command(['ffmpeg', '-version']).splitlines()[0]
    versions['ffprobe'] = command(['ffprobe', '-version']).splitlines()[0]
    record = {'label': label, 'saved_at_utc': stamp, 'source_file': source.name,
              'source_url_or_description': source_url, 'sha256': source_hash,
              'method': detector.NAME, 'description': detector.DESCRIPTION,
              'parameters': parameters, 'threshold': threshold, 'minimum_gap_s': gap,
              'analysis_width': width, 'manual_cuts_s': marked, 'observations': observations,
              'cuts_s': cuts, 'shots': shots, 'average_shot_length_s': result['duration'] / len(shots),
              'timing_policy': 'ffprobe PTS relative to first frame; last frame duration or previous interval',
              'selection_policy': 'first score strictly above threshold after minimum gap from previous cut or start',
              'versions': versions, **result}
    (folder / 'run.json').write_text(json.dumps(record, indent=2, allow_nan=False) + '\n')
    # Snapshot all local Python modules, including any added algorithm variants.
    for module in ROOT.glob('*.py'):
        (folder / module.name).write_text(module.read_text())
    (folder / 'requirements-lock.txt').write_text(command([__import__('sys').executable, '-m', 'pip', 'freeze']))
    with (folder / 'shots.csv').open('w', newline='') as output:
        writer = csv.DictWriter(output, fieldnames=list(shots[0]))
        writer.writeheader()
        writer.writerows(shots)
    st.success(f'Saved {folder.relative_to(ROOT)}. Media and previews stay outside git; inspect the text evidence before committing.')
