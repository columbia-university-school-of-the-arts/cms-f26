"""Run with the lab dependencies installed: python -m unittest discover -s tests."""
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


if __name__ == '__main__':
    unittest.main()
