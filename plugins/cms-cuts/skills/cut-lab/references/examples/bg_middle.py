"""Phase-2 example adapted from BG's Behrang-Garakani-scene-detect-test1.py.

Same grayscale changed-pixel criterion, vectorized with OpenCV/NumPy.
The original's fixed tolerance (>10) is exposed as a slider. The original
compares native-resolution frames; the app's analysis width is an additional
experimental choice. Set minimum gap to zero for its boundary selection rule.
"""
import cv2
import numpy as np

NAME = "BG's center-region changed pixels"
DESCRIPTION = "Count grayscale pixels whose change exceeds a tolerance, within a centered crop. The score is a percentage (0–100)."
THRESHOLD = {"min": 0.0, "max": 100.0, "default": 20.0, "step": 0.5,
             "help": "Declare a cut when the percentage of changed crop pixels is strictly greater than this."}
PARAMETERS = {
    "Center width and height (%)": {
        "min": 1, "max": 100, "default": 50, "step": 1,
        "help": "50% width × 50% height covers 25% of the image area; 100 uses the whole frame."},
    "Pixel brightness tolerance": {
        "min": 0, "max": 255, "default": 10, "step": 1,
        "help": "A pixel counts as changed only if its grayscale difference is strictly greater than this value (0–255)."},
}


def crop_bounds(frame, percentage):
    h, w = frame.shape[:2]
    # The old script could produce an empty crop for very small percentages.
    ch, cw = max(1, int(h * percentage / 100)), max(1, int(w * percentage / 100))
    y, x = (h - ch) // 2, (w - cw) // 2
    return x, y, cw, ch


def score_pair(previous, current, parameters):
    x, y, w, h = crop_bounds(current, parameters['Center width and height (%)'])
    a = cv2.cvtColor(previous[y:y+h, x:x+w], cv2.COLOR_BGR2GRAY)
    b = cv2.cvtColor(current[y:y+h, x:x+w], cv2.COLOR_BGR2GRAY)
    return float(100 * np.mean(cv2.absdiff(a, b) > parameters['Pixel brightness tolerance']))


def inspect_frame(rgb_frame, parameters):
    """Draw the selected crop on a copy of the RGB inspection frame."""
    frame = rgb_frame.copy()
    x, y, w, h = crop_bounds(frame, parameters['Center width and height (%)'])
    cv2.rectangle(frame, (x, y), (x + w - 1, y + h - 1), (255, 165, 0), 2)
    return frame
