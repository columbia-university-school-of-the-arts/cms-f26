"""Replace this adapter only after recording the student's own rule."""
NAME = "Our invented rule"
DESCRIPTION = "Describe what changes between two frames and why it counts as a cut."
THRESHOLD = {"min": 0.0, "max": 1.0, "default": 0.2, "step": 0.01,
             "help": "Set the score's units and range when implementing your rule."}
# Each feature slider: min, max, default, step, help. Add only useful controls.
PARAMETERS = {}


def score_pair(previous, current, parameters):
    """BGR uint8 frames, same dimensions. Return a finite scalar change score.

    Larger means more change. Frames are resized to the app's analysis width.
    The score is assigned to the current frame's presentation timestamp.
    """
    raise NotImplementedError("State your rule first, then ask Claude to implement it in detector.py.")
