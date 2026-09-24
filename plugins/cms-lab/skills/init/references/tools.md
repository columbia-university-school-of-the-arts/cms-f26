# The lab's tools, by week

The one list of everything a student's machine needs for the course. `init`
works through every row, in order, whatever week it is; a student who missed
weeks runs `/cms-lab:init` once and catches up. Rows are only ever added.
When a week brings a new tool, add its row here and bump the plugin version.

Claude Code itself is a prerequisite: `init` cannot install the thing it runs
in. A student without it follows the hub README's setup section first.

| Week | Tool | Check (must succeed) | macOS | Windows (inside WSL) | Needed by |
|---|---|---|---|---|---|
| 2 | Homebrew (macOS only) | `brew --version` | Hub README's `setup.sh`; never install Homebrew from here | — | every macOS install below |
| 2 | git | `git --version` | `brew install git` | `sudo apt install -y git` | the fleet repository |
| 2 | GitHub CLI | `gh --version` | `brew install gh` | the hub's `setup-wsl.sh` | the fleet repository |
| 2 | GitHub sign-in | `gh auth status` | hand over `gh auth login`, then `gh auth setup-git` | same | the fleet repository |
| 3 | Python 3.10+ with venv | `python3 --version` and `python3 -m venv --help` | `brew install python` | `sudo apt install -y python3 python3-venv python3-pip` | every lab project |
| 3 | FFmpeg and FFprobe | `ffmpeg -version` and `ffprobe -version` | `brew install ffmpeg` | `sudo apt install -y ffmpeg` | scene-detect |
| 3 | JavaScript runtime for yt-dlp | `deno --version`, else `node --version` | `brew install deno` | Deno's official installer, shown first; see the yt-dlp EJS page for supported runtimes and versions | scene-detect |
| 3 | ImageMagick, with a font for text | `magick -version`, else `convert -version`; then render a word with the font file (see note) | `brew install imagemagick`; font `/System/Library/Fonts/Supplemental/Arial.ttf` ships with macOS | `sudo apt install -y imagemagick fonts-dejavu-core`; font `/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf` | scene-detect, for students who choose to put text on screen |

Notes on rows:

- **GitHub sign-in** is interactive. Hand `gh auth login` to the student
  (choose GitHub.com, HTTPS, yes to authenticating git, log in with a web
  browser), then `gh auth setup-git`. Do not fix a sign-in to the wrong
  account yourself; say what `gh auth status` reports.
- **FFmpeg** is slow to install through Homebrew. Say so, and let the student
  do the week's by-hand work meanwhile.
- **JavaScript runtime:** yt-dlp uses Deno by default. A Node that meets the
  yt-dlp EJS page's minimum is acceptable; record it, since yt-dlp then needs
  `--js-runtimes node`. <https://github.com/yt-dlp/yt-dlp/wiki/EJS>
- **ImageMagick** is how a student may write text on screen: titles, shot
  numbers, timestamps. Homebrew installs ImageMagick 7 (`magick`); Ubuntu's
  package may still be ImageMagick 6 (`convert`, no `magick`), which takes the
  same arguments. A version alone proves nothing here: Homebrew's build
  registers no fonts, so text fails with "unable to read font" until a font
  file is named. The check therefore renders a word with the platform's font
  file and must exit cleanly:
  `magick -size 120x40 xc:black -font FONT -fill white -pointsize 24 -annotate +8+30 Cut null:`
  (with `convert` in place of `magick` on ImageMagick 6). Record the font
  path in `lab-setup.md`; projects pass it as `-font`, and FFmpeg's `drawtext`
  filter accepts the same file as `fontfile=`.
- Python packages never go here. Each project installs its own into its own
  `.venv` under `~/cms-lab/<project>/`.
