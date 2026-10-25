"""Run with the lab dependencies installed: python -m unittest discover -s tests."""
import csv
import json
import importlib.util
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

import cv2
import numpy as np

ASSETS = Path(__file__).resolve().parents[1] / 'skills/scene-detect/assets/lab'
sys.path.insert(0, str(ASSETS))
import lab


class LabTest(unittest.TestCase):
    def test_bg_center_rule(self):
        spec = importlib.util.spec_from_file_location('bg_middle', ASSETS.parents[1] / 'references/examples/bg_middle.py')
        method = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(method)
        a = np.zeros((4, 4, 3), dtype=np.uint8)
        b = a.copy()
        b[1, 1] = 255
        params = {'Center width and height (%)': 50, 'Pixel brightness tolerance': 10}
        self.assertEqual(method.crop_bounds(a, 50), (1, 1, 2, 2))
        self.assertEqual(method.score_pair(a, b, params), 25.)
        b[1, 1] = 10
        self.assertEqual(method.score_pair(a, b, params), 0.)
        b[1, 1] = 11
        self.assertEqual(method.score_pair(a, b, params), 25.)
        b = a.copy()
        b[0, 0] = 255
        self.assertEqual(method.score_pair(a, b, params), 0.)
        self.assertEqual(method.score_pair(a, a, params), 0.)
        self.assertEqual(method.inspect_frame(a, params).shape, a.shape)

    def test_threshold_and_short_shots(self):
        self.assertEqual(lab.boundaries([0, .1, .2, .3], [0, .5, .6, .9], .5, .2), [.2])
        self.assertEqual(lab.boundaries([0, .1, .2], [0, 1, 1], .5, 0), [.1, .2])
        shots = lab.shot_table([], 3)
        self.assertEqual(shots, [{'shot': 1, 'start_s': 0., 'end_s': 3, 'length_s': 3.}])
        with self.assertRaises(ValueError):
            lab.shot_table([float('nan')], 3)

    def test_source_url_from_download_record(self):
        with tempfile.TemporaryDirectory() as tmp:
            video = Path(tmp) / 'abc.mp4'
            self.assertEqual(lab.source_url(video), '')
            video.with_suffix('.info.json').write_text(json.dumps({'webpage_url': 'https://example.org/v/abc'}))
            self.assertEqual(lab.source_url(video), 'https://example.org/v/abc')

    def test_video_measurement_and_ffmpeg_evidence(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'three-shots.mp4'
            writer = cv2.VideoWriter(str(path), cv2.VideoWriter_fourcc(*'mp4v'), 10, (64, 48))
            self.assertTrue(writer.isOpened())
            for value in [0, 255, 0]:
                for _ in range(10):
                    writer.write(np.full((48, 64, 3), value, dtype=np.uint8))
            writer.release()
            result = lab.analyze(path, 160, {}, lambda a, b, p: float(cv2.absdiff(a, b).mean() / 255))
            cuts = lab.boundaries(result['times'], result['scores'], .5, .2)
            self.assertEqual(cuts, [1., 2.])
            self.assertAlmostEqual(result['duration'], 3.)
            rows = lab.shot_table(cuts, result['duration'])
            self.assertEqual([r['length_s'] for r in rows], [1., 1., 1.])
            before, after = lab.boundary_frames(path, 10)
            self.assertLess(before.mean(), 5)
            self.assertGreater(after.mean(), 245)
            clip = lab.export_clip(path, 1, 2, Path(tmp) / 'shot.mp4')
            self.assertAlmostEqual(lab.timing(clip)['duration'], 1, places=2)
            cap = cv2.VideoCapture(str(clip))
            frames = []
            while True:
                ok, frame = cap.read()
                if not ok:
                    break
                frames.append(frame.mean())
            cap.release()
            self.assertEqual(len(frames), 10)
            self.assertTrue(all(mean > 245 for mean in frames))
            with self.assertRaises(ValueError):
                lab.analyze(path, 160, {}, lambda a, b, p: float('nan'))

    def test_interface_in_isolated_student_copy(self):
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / 'lab'
            shutil.copytree(ASSETS, dest)
            media = dest / 'media'
            media.mkdir()
            path = media / 'test.mp4'
            writer = cv2.VideoWriter(str(path), cv2.VideoWriter_fourcc(*'mp4v'), 10, (64, 48))
            for value in [0, 255, 0]:
                for _ in range(10):
                    writer.write(np.full((48, 64, 3), value, dtype=np.uint8))
            writer.release()
            # A test-only rule. The marketplace ships the unanswered adapter.
            detector = dest / 'detector.py'
            detector.write_text(detector.read_text().replace(
                'raise NotImplementedError("State your rule first, then ask Claude to implement it in detector.py.")',
                'return abs(current.astype(float) - previous.astype(float)).mean() / 255'))
            script = '''
from pathlib import Path
import json
from streamlit.testing.v1 import AppTest
at = AppTest.from_file('app.py', default_timeout=30).run()
assert not at.exception, at.exception
assert at.metric[0].value == '2'
assert at.metric[1].value == '3'
assert at.metric[2].value == '1.000 s'
at.checkbox[0].check().run()
assert not at.exception, at.exception
at.checkbox[1].check().run()
at.checkbox[2].check().run()
assert not at.exception, at.exception
assert at.button[0].disabled  # no source recorded yet
at.text_input[0].set_value('https://example.org/test-clip').run()
at.button[0].click().run()
assert not at.exception, at.exception
runs = list(Path('runs').glob('*/run.json'))
assert len(runs) == 1
r = json.loads(runs[0].read_text())
assert r['cuts_s'] == [1, 2]
assert r['source_url_or_description'] == 'https://example.org/test-clip'
assert r['sha256'] and r['versions']['ffmpeg']
assert (runs[0].parent / 'shots.csv').is_file()
assert (runs[0].parent / 'detector.py').is_file()
next(s for s in at.slider if s.label == 'Cut threshold').set_value(1.0).run()
assert not at.exception, at.exception
assert at.metric[0].value == '0'
'''
            (dest / 'exercise_test.py').write_text(script)
            result = subprocess.run([sys.executable, 'exercise_test.py'], cwd=dest, capture_output=True, text=True, timeout=120)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)



class FrameDiffTest(unittest.TestCase):
    def test_make_test_clip_end_to_end(self):
        script = Path(__file__).resolve().parents[1] / 'skills/frame-diff/assets/lab/framediff.py'
        with tempfile.TemporaryDirectory() as tmp:
            result = subprocess.run([sys.executable, str(script), '--make-test', '-o', 'out/test.mp4'],
                                    cwd=tmp, capture_output=True, text=True, timeout=300)
            self.assertEqual(result.returncode, 0, result.stderr[-2000:])
            out = Path(tmp) / 'out/test.mp4'
            rows = list(csv.DictReader(open(out.with_suffix('.csv'))))
            self.assertEqual(len(rows), 210)  # 7 s at 30 fps, every frame once
            self.assertTrue(all(r['type'] == 'P' for r in rows))
            size = [int(r['bytes']) for r in rows]
            # Frame 0 has nothing to copy from; after it, the hard cut at 4 s costs the most
            self.assertGreater(size[0], 3 * sorted(size)[105])
            self.assertEqual(max(range(1, 210), key=lambda i: size[i]), 120)
            self.assertEqual(rows[0]['R_change_pct'], '0.0000')

            # Mid-shot the encoder copies the static bars; at the cut it sends the picture
            copied = [float(r['copied_pct']) for r in rows]
            self.assertGreater(copied[60], 80)
            self.assertLess(copied[120], 30)

            def panel(n, col):
                raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', str(out), '-vf', f'select=eq(n\\,{n})',
                                      '-fps_mode', 'passthrough', '-frames:v', '1',
                                      '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'],
                                     capture_output=True, check=True).stdout
                frame = np.frombuffer(raw, np.uint8).reshape(764, 1920, 3).astype(int)
                return frame[84:444, col * 640:(col + 1) * 640]

            # The decoded panel keeps its colour: saturated bars, R, G and B far apart
            decoded = panel(60, 0)
            self.assertGreater((decoded.max(axis=2) - decoded.min(axis=2)).mean(), 60)
            # The heat panel is dark where the encoder copied and bright at the cut
            self.assertLess(panel(60, 1).mean(), 40)
            self.assertGreater(panel(120, 1).mean(), 100)

    def test_panels_stay_in_step_at_23976_fps(self):
        # Film-rate clips once put the piped panels a frame behind on a third of frames
        script = Path(__file__).resolve().parents[1] / 'skills/frame-diff/assets/lab/framediff.py'
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / 'film.mp4'
            subprocess.run(['ffmpeg', '-v', 'error', '-f', 'lavfi', '-i', 'testsrc2=s=640x360:r=24000/1001:d=2',
                            '-f', 'lavfi', '-i', 'mandelbrot=s=640x360:r=24000/1001,trim=duration=1',
                            '-filter_complex', '[0:v][1:v]concat=n=2:v=1[v]', '-map', '[v]',
                            '-c:v', 'libx264', '-pix_fmt', 'yuv420p', str(src)], check=True)
            result = subprocess.run([sys.executable, str(script), str(src), '-o', 'out/film.mp4'],
                                    cwd=tmp, capture_output=True, text=True, timeout=300)
            self.assertEqual(result.returncode, 0, result.stderr[-2000:])
            out = Path(tmp) / 'out/film.mp4'
            rows = list(csv.DictReader(open(out.with_suffix('.csv'))))
            raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', str(out), '-vf', 'crop=1280:360:0:84',
                                  '-f', 'rawvideo', '-pix_fmt', 'gray', '-'], capture_output=True, check=True).stdout
            d = np.frombuffer(raw, np.uint8).reshape(-1, 360, 1280).astype(int)
            self.assertEqual(len(d), len(rows))
            dec, heat = d[:, :, :640], d[:, :, 640:]
            change = [np.abs(dec[i] - dec[i - 1]).mean() for i in range(1, len(d))]
            self.assertFalse([i for i, c in enumerate(change, 1) if c < 0.3], 'a decoded frame repeats')
            cut = int(np.argmax(change)) + 1
            sizes = [int(r['bytes']) for r in rows]
            self.assertEqual(cut, max(range(1, len(rows)), key=lambda i: sizes[i]))
            self.assertEqual(cut, int(np.argmax([heat[i].mean() for i in range(1, len(d))])) + 1)

    def test_view_all_two_rows_and_prediction(self):
        lab = Path(__file__).resolve().parents[1] / 'skills/frame-diff/assets/lab'
        with tempfile.TemporaryDirectory() as tmp:
            result = subprocess.run([sys.executable, str(lab / 'framediff.py'), '--make-test',
                                     '--view', 'all', '-o', 'out/all.mp4'],
                                    cwd=tmp, capture_output=True, text=True, timeout=300)
            self.assertEqual(result.returncode, 0, result.stderr[-2000:])
            out = Path(tmp) / 'out/all.mp4'
            layout = json.loads(out.with_suffix('.json').read_text())
            self.assertEqual(layout['sources'], [['prev', 'mv', 'heat'], ['pred', 'amp', 'dec']])
            raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', str(out), '-vf', 'select=eq(n\\,60)',
                                  '-fps_mode', 'passthrough', '-frames:v', '1',
                                  '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], capture_output=True, check=True).stdout
            frame = np.frombuffer(raw, np.uint8).reshape(2 * (84 + 360) + 320, 1920, 3).astype(int)
            row2 = frame[84 + 360 + 84:84 + 360 + 84 + 360]
            pred, dec = row2[:, :640], row2[:, 1280:]
            # Mid-shot the prediction is nearly the whole decoded frame
            self.assertLess(np.abs(pred - dec).mean(), 6)
            # At the cut (frame 120) the previous-frame panel still shows frame 119's
            # colour bars, while the decoded panel is already the fractal
            raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', str(out),
                                  '-vf', 'select=between(n\\,119\\,120)', '-fps_mode', 'passthrough',
                                  '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], capture_output=True, check=True).stdout
            pair = np.frombuffer(raw, np.uint8).reshape(2, 2 * (84 + 360) + 320, 1920, 3).astype(int)
            prev_120 = pair[1, 84:444, :640]
            dec_119 = pair[0, 84 + 360 + 84:84 + 360 + 84 + 360, 1280:]
            dec_120 = pair[1, 84 + 360 + 84:84 + 360 + 84 + 360, 1280:]
            self.assertLess(np.abs(prev_120 - dec_119).mean(), 5)
            self.assertGreater(np.abs(prev_120 - dec_120).mean(), 50)
            report = subprocess.run([sys.executable, str(lab / 'frame_report.py'), str(out), '120'],
                                    cwd=tmp, capture_output=True, text=True, check=True)
            self.assertIn('frame 120:', report.stdout)
            self.assertTrue((Path(tmp) / 'out/all_frames/frame_00120_row2_pred.png').is_file())

if __name__ == '__main__':
    unittest.main()
