# Set up the local lab

Work in the local lab folder, not a repository. Copy the sibling `assets/lab`
directory to `~/cms-lab/scene-detect` once. Commands below run there.
No API key, hosted service, or model inference is needed by the app.

Before installing, explain and record what will run. On macOS, use Homebrew:

```sh
brew install python ffmpeg deno
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
```

On Windows work inside the existing WSL environment: use `sudo apt update`
and `sudo apt install python3-venv ffmpeg`, then the same venv commands.
YouTube also needs a supported JavaScript runtime. Check `deno --version` or
`node --version`; use the current yt-dlp EJS instructions below to install a
supported runtime if absent. For Node, pass `--js-runtimes node` to yt-dlp.
Do not execute a downloaded installer without showing it to the student.

Your shell cannot answer a password prompt or any other interactive question.
Hand such a command to the student rather than running it: `sudo apt …` in WSL
always, and any `brew` step that asks for the Mac password. Hand over any
command that fails for want of permission, too, or that the student declined
but still needs. Say why, give the exact line in a code block, and tell them:
open a second Terminal window (⌘-N on a Mac; a new Ubuntu window on Windows),
paste it there, type your password if asked (nothing shows while you type),
and tell me when it finishes or paste back any error. Wait. Then verify it
yourself with the version checks below before continuing. Never ask the student
to type their password into this conversation.

BG shares the class clip through Courseworks. Teach its download as an
explicit terminal action before opening the app:

```sh
mkdir -p media
.venv/bin/python -m yt_dlp --no-playlist --max-downloads 1 -f 'bv*[height<=720]+ba/b[height<=720]' -S 'vcodec:h264,res:720,acodec:m4a' --merge-output-format mp4 --write-info-json -o 'media/%(id)s.%(ext)s' 'https://www.youtube.com/watch?v=-1tza4BxVfA'
```

Explain format selection, the output path, and why merging needs FFmpeg.
The `-S` sort prefers H.264 video and AAC audio, which every browser plays;
YouTube otherwise picks AV1, which Safari plays only on recent Macs.
`--max-downloads 1` can report the limit reached after successfully saving the
one video; inspect the output rather than retrying blindly. `--merge-output-format`
sets the container when merging; a single-stream fallback may keep its own
extension. Select the actual downloaded file in the app. The app also accepts
a local file upload, including a student's own clip, but does not hide the
YouTube download behind a URL box.

Check `ffmpeg -version`, `ffprobe -version`, and
`.venv/bin/python -m yt_dlp --version`. If YouTube rejects the download, check
the runtime and current yt-dlp release once. Stop and show the error if it
still fails. Do not automatically extract browser cookies or bypass access
controls. Downloads and generated clips stay local.

After Claude implements the student's rule:

```sh
.venv/bin/python -m streamlit run app.py --server.address 127.0.0.1
```

Streamlit prints a local URL. On WSL open that URL in the Windows browser.
Sliders rerun the score pass when feature parameters change; threshold and
minimum-gap adjustments reuse the scores. To load edited detector code,
restart the server. The app streams frame pairs rather than retaining the
whole decoded video. It targets short classroom clips.

The scaffold uses actual frame presentation times from ffprobe; it checks
that OpenCV decoded the same number of frames. This avoids deriving times
from a nominal frame rate on variable-frame-rate input. The final frame uses
its reported duration (or the previous frame interval if missing); the export
records that timing policy. A decode mismatch stops analysis visibly.

Dependencies are bounded in `requirements.txt` for fresh installs. Each saved
run includes the exact installed versions and Python version; also capture
`pip freeze > requirements-lock.txt` after a successful classroom setup.
FFmpeg's build-dependent license is in `ffmpeg -L`; log the actual build.

Sources checked 23 September 2026:

- [yt-dlp installation, formats and dependencies](https://github.com/yt-dlp/yt-dlp#readme)
- [YouTube JavaScript runtime support](https://github.com/yt-dlp/yt-dlp/wiki/EJS)
- [FFmpeg seeking and output options](https://www.ffmpeg.org/ffmpeg.html)
- [Streamlit video playback](https://docs.streamlit.io/develop/api-reference/media/st.video)
