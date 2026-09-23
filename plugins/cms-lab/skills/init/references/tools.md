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
- Python packages never go here. Each project installs its own into its own
  `.venv` under `~/cms-lab/<project>/`.
