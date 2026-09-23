# Cut-detector ingredients — released after the invented rule

A detector is a combination of choices. There is no requirement to choose one
complete named method. Keep your first rule, then use these ingredients to
explain it, change it, or invent another combination.

Start with this sentence and fill it in:

> Look at **___** of the frame, represent it as **___**, measure **___**
> between frames, and call it a cut when **___**. Check the claim by **___**.

For every ingredient you add, say what it lets your rule notice and what it
makes easier to overlook. You do not need one from every row or every group.
Use a small combination you can explain, then change one ingredient at a time.
The controls below are candidates, not a requirement to expose every knob.

## 1. Where and when to look

| Ingredient | Definition | Useful controls | What the choice can hide |
|---|---|---|---|
| Whole frame | Measure the entire visible image. | None beyond the measurement's settings | Borders, subtitles, logos and moving backgrounds also count. |
| Region of interest (ROI) | Measure only a chosen rectangle, such as the center. | Crop width, height and position | A cut may change material outside the rectangle. Half the width and half the height is one quarter of the area. |
| Spatial grid | Divide the frame into blocks and measure them separately. | Rows, columns; later choose how to combine block scores | Block size changes what counts as a local event; motion crosses block boundaries. |
| Resize | Reduce the number of pixels before measurement. | Analysis width in pixels | Fine details disappear; the same rule can give a different score. This changes space, not time. |
| Frame sampling | Compare only selected frames rather than every frame. | Sampling interval in frames or seconds | Short shots can disappear between samples. Report actual sampled timestamps; a sampled boundary is only localized to an interval. The scaffold defaults to every frame. |
| Temporal window | Use several frames before/after a moment. | Window radius or duration | Nearby cuts influence each other; use of future frames adds delay to a live detector. Requires extending the pair-only adapter. |

## 2. What a frame is represented as

A **representation** is what information you keep before comparing two frames.

| Ingredient | Definition | Useful controls | What is discarded or emphasized |
|---|---|---|---|
| Grayscale | One intensity value per pixel, computed from color channels. | Conversion convention | Color differences can vanish even when colors look distinct. OpenCV's conversion is weighted, not simply the average of R, G and B. |
| RGB or HSV channels | RGB separates red, green and blue; HSV separates hue (color), saturation (color intensity) and value (brightness). | Channels and weights | Hue is circular: values near its two ends can be similar colors. OpenCV inputs are BGR; explicitly convert before interpreting channels. |
| Blurred image | Average information over a small neighborhood before measuring. | Blur size, Gaussian sigma | Noise falls, but small details and sharp edges also disappear. |
| Color histogram | Count how many pixels fall into each color/intensity range, ignoring their position within the region. | Color space, number of bins, normalization | Two different compositions can contain the same colors. A histogram can be global or computed per grid block. |
| Edge map | Mark locations where intensity changes sharply within one frame, such as object outlines. Canny is one way to find them. | Canny low/high thresholds, smoothing | Edges are not cuts: the map describes one frame. Camera motion shifts its outlines. Canny thresholds are not the cut threshold. |
| Perceptual hash | Compress a frame's visual appearance into a short bit pattern so similar frames tend to have similar codes. | Hash family (pHash/dHash), size | Different scenes can have similar codes; a perceptual hash is not a cryptographic identity check. |

## 3. What difference to measure

A **score** is a number describing change. Decide its units and direction:
in this scaffold, a larger score must mean more change.

| Ingredient | Definition | Units and useful controls | A question to test |
|---|---|---|---|
| Absolute pixel difference | Subtract aligned pixel/channel values, take absolute values, then average. | 0–255 for 8-bit values, or 0–1 if divided by 255; channel weights | Does a camera pan produce a large score without a cut? Use signed arithmetic or OpenCV absdiff to avoid unsigned wraparound. |
| Squared pixel difference | Square each difference before averaging, emphasizing large changes. | 0–65025 for 8-bit values; normalization convention | Does a small bright flash dominate the measurement? |
| Changed-pixel fraction | First call each pixel changed if its difference exceeds a tolerance; then count the fraction that changed. | Either 0–1 or 0–100%; pixel tolerance and later cut threshold are separate controls | Is a small moving object enough? Which changes does the pixel tolerance ignore? |
| Histogram distance | Compare two distributions of color counts rather than matching pixels at the same positions. | Metric and binning; normalize counts first. Bhattacharyya/Hellinger distance for normalized histograms is 0–1; chi-square has a different scale. | Can two shots with the same palette look unchanged to this rule? Correlation/intersection are similarities: transform their direction before using this scaffold. |
| Edge-map difference | Count edge locations that differ between the frames. | Fraction or count of disagreeing edge pixels; choose the denominator explicitly | Will a small movement shift many edges? |
| Edge change ratio | Count new edges without a nearby old edge, and disappearing edges without a nearby new edge; combine these proportions. | Spatial tolerance/dilation radius; entering/exiting proportions; specify max or other combination | Does allowing nearby matches reduce motion false alarms? Define empty-edge cases rather than dividing by zero. |
| Structural similarity (SSIM) | Compare local luminance, contrast and structure. It starts as a similarity score. | Window size, data range; transform to a change score such as 1 − SSIM and declare its range | Can similar layouts across a real cut hide it? Do not assume 1 − SSIM can never exceed 1. |
| Hash distance | Count differing bits between perceptual hashes (Hamming distance). | Bit count or fraction of bits; hash size | Does increasing hash detail distinguish the missed cut? |
| Motion-compensated residual | Estimate how content moved, align the frames, then measure the change left over. | Motion estimation, alignment and residual settings | Did alignment fail, or is there a cut? Optical flow estimates pixel motion; feature matching aligns recognizable points. This needs more implementation work. |
| Brightness over time | Follow a frame's aggregate brightness across several moments. | Brightness threshold and duration | Useful for fades or black intervals; a dark shot is not automatically a transition. |

## 4. How local evidence becomes one decision

| Ingredient | Definition | Useful controls | The judgement built into it |
|---|---|---|---|
| Mean aggregation | Average pixel, channel or block scores. | Weights if justified | Small localized changes can be diluted. |
| Maximum or percentile | Keep the largest score, or a chosen point in the score distribution. | Percentile; block size if using blocks | A small disturbance may dominate; a high percentile and a mean answer different questions. |
| Fixed threshold | Declare a cut when a change score exceeds one number. | Cut threshold, in the score's units | The same number may not suit both quiet and action-heavy passages. |
| Adaptive threshold | Compare a score with its local temporal baseline, rather than only a fixed number. | Window, ratio or offset, minimum absolute score | Define a zero baseline; one nearby edit can raise the baseline for another. |
| Minimum gap | Suppress new detections too soon after the last accepted boundary. | Seconds or frames | This encodes a belief about how short a shot may be. The scaffold keeps the first qualifying boundary, not necessarily the strongest. |
| Peak selection | Select a local score maximum rather than every high-scoring frame. | Neighborhood and tie-breaking | Several high frames may become one event; the timestamp can move. |
| Combined evidence | Require multiple signals (AND), accept any (OR), or combine their scores with declared weights. | Logical rule or weights; score normalization | AND can miss cuts; OR can add false alarms. Do not add a percentage to an unscaled squared difference and call the sum meaningful. |
| Persistence / two thresholds | Require evidence for several frames, or use separate start/end thresholds to group an event. | Duration; start/end thresholds | Useful for gradual events, but can miss a one-frame hard cut. A dissolve may need a start/end interval instead of one timestamp. |

## 5. Open-source tools that supply ingredients

Use NumPy for array arithmetic and aggregation; OpenCV for decoding, color
conversion, crops, histograms, edges, motion and alignment; scikit-image for
SSIM; and ImageHash/Pillow for perceptual hashes. Install only what your chosen
combination uses, and record versions, licenses and sources in the ledgers.

FFmpeg supplies trimming and playback evidence, and also has built-in scene
scores (`scdet` / `select`) and black-interval detection (`blackdetect`) that
can be investigated as comparisons. Their defaults are choices too.

**Later comparisons and extensions:** PySceneDetect combines several of these
choices in ready-made detectors. TransNet V2 uses a learned model to produce
boundary predictions; it brings model weights, training assumptions and a
larger runtime. Neither is needed for the initial experiment, and neither is
a definition of a correct cut. Save them for the final comparison or an
extension, as BG directs.

## Build a combination and inspect it

After choosing, ask Claude to restate the combination in your own terms before
implementing it. Preserve your invented rule. Add controls with units and an
explanation of their effect; show intermediate evidence when useful, such as
the ROI, edges, histograms or score components. A temporal rule needs access to
a sequence; extend the adapter rather than quietly replacing your idea with a
pairwise approximation.

Predict the result on a tiny example, check the arithmetic, then run the clip.
Change one ingredient or parameter and save both runs. Inspect FFmpeg footage
around detections, and watch within predicted shots to find missed cuts.
A larger or smaller average shot length does not tell you which run is right.

## BG's example: changed pixels in the center

`examples/bg_middle.py` adapts BG's `Behrang-Garakani-scene-detect-test1.py`,
provided for this workshop. Offer it only after the first experiment. Preserve
the invented detector and its saved run before copying this adapter into
`detector.py`; restart the app to load it. It supplies three sliders and marks
the selected crop on the side-by-side inspection frames.

Its defaults reproduce the original measurement: take the middle 50% of width
and height, convert to grayscale, count pixels whose absolute difference is
strictly greater than 10, and propose a cut when more than 20% have changed.
Half of each dimension is one quarter of the area. The new adapter replaces
the nested pixel loops with equivalent array operations and exposes the
previously fixed tolerance. A one-pixel minimum prevents empty crops.

For matching the original's full-frame analysis, select **native** analysis
width and set minimum gap to zero. The old `--fps` option skipped frames; this
scaffold analyzes every decoded frame and uses presentation timestamps. If
sampling is explored later, record the actual sampling interval and discuss
boundaries that can fall between sampled frames. Do not describe the old
requested FPS as necessarily its effective sampling rate.

Keep two questions separate: did the implementation calculate the chosen rule
correctly, and does that rule recognize the cuts a viewer sees? A correct
changed-pixel calculation can still mistake camera movement for an edit.
Credit BG's source in the ledgers when borrowing its code or idea.

## PySceneDetect: final comparison only

Once BG calls this phase, install `scenedetect-headless` in the lab venv, record
its version and license, and inspect `scenedetect --help` plus the chosen
subcommand's help. Select ContentDetector, AdaptiveDetector, HistogramDetector
or HashDetector for a comparison that bears on the student's experiment.
The official API/CLI docs below describe the current interfaces; do not assume
the package installed locally matches the documentation's latest version.

Save its intervals and parameters under a separately named run. The same source
file, zero-based origin and first-frame-of-new-shot convention must apply.
Add its boundaries to the shared plot or import them as a separate result,
then use the app's FFmpeg export function to inspect disagreements. Compare
false alarms and missed cuts against the manual marks, with a declared timing
tolerance and one-to-one matching if computing precision/recall. Neither
PySceneDetect nor the manual pass is an oracle.

## Sources

Primary implementation references, checked 23 September 2026:

- [OpenCV histogram comparison and distance definitions](https://docs.opencv.org/4.x/d8/dc8/tutorial_histogram_comparison.html)
- [OpenCV Canny edge detection](https://docs.opencv.org/4.x/da/d22/tutorial_py_canny.html)
- [OpenCV optical flow](https://docs.opencv.org/4.x/d4/dee/tutorial_optical_flow.html)
- [scikit-image image metrics, including SSIM](https://scikit-image.org/docs/stable/api/skimage.metrics.html)
- [ImageHash source and algorithms](https://github.com/JohannesBuchner/imagehash)
- [FFmpeg filters, including scdet and blackdetect](https://ffmpeg.org/ffmpeg-filters.html)
- [PySceneDetect detector APIs](https://www.scenedetect.com/docs/head/api/detectors.html)
- [TransNet V2 source, paper and pretrained models](https://github.com/soCzech/TransNetV2)
