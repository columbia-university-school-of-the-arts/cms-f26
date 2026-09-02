#!/usr/bin/env bash
#
# Coding for Media Studies (CMS 2026) — toolchain setup, Windows via WSL.
#
# Run this INSIDE your WSL terminal (Ubuntu), not in PowerShell.
# If you have not installed WSL yet, see WINDOWS.md first.
#
# Installs, in order: git, the GitHub CLI, ffmpeg, Claude Code.
# Safe to run more than once. Anything already installed is reported and
# skipped rather than reinstalled.
#
#   ./setup-wsl.sh --dry-run    show every command without running any of them
#   ./setup-wsl.sh              do it
#   ./setup-wsl.sh --check      only report what is already present
#
# Why this exists, and why it is not a PowerShell script:
#
# On native Windows, git and the GitHub CLI both demand administrator rights,
# which a script cannot grant and a college loaner laptop may not give you.
# Inside WSL you are root in your own Linux, so `sudo apt install` just works
# and that wall disappears. The only step that may still need administrator
# rights is installing WSL itself, which happens once, before this script.
#
# This script asks for your WSL password when it uses sudo. That password is
# the one you chose when you set up Ubuntu — it is not your Windows password
# and not your GitHub password.

set -uo pipefail

# Bumped by hand. Printed on every run so that a stale copy is visible in the
# room rather than inferred from odd behaviour. Keep in step with setup.sh.
SETUP_VERSION="2026.09.02"

DRY_RUN=0
CHECK_ONLY=0
for arg in "$@"; do
  case "$arg" in
    --dry-run) DRY_RUN=1 ;;
    --check)   CHECK_ONLY=1 ;;
    -h|--help) sed -n '2,28p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
    *) echo "unknown option: $arg (try --help)" >&2; exit 2 ;;
  esac
done

# ---------------------------------------------------------------- output ----

if [ -t 1 ]; then
  B=$'\033[1m'; DIM=$'\033[2m'; GREEN=$'\033[32m'; YELLOW=$'\033[33m'
  RED=$'\033[31m'; OFF=$'\033[0m'
else
  B=""; DIM=""; GREEN=""; YELLOW=""; RED=""; OFF=""
fi

step()  { printf '\n%s==>%s %s%s%s\n' "$B" "$OFF" "$B" "$1" "$OFF"; }
have()  { printf '  %sok%s   %s\n' "$GREEN" "$OFF" "$1"; }
todo()  { printf '  %s--%s   %s\n' "$YELLOW" "$OFF" "$1"; }
warn()  { printf '  %s!!%s   %s\n' "$RED" "$OFF" "$1"; }
note()  { printf '       %s%s%s\n' "$DIM" "$1" "$OFF"; }

run() {
  if [ "$DRY_RUN" = 1 ]; then
    printf '       %s$ %s%s\n' "$DIM" "$*" "$OFF"
    return 0
  fi
  "$@"
}

# The fetch MUST happen inside the guard. Writing run bash -c "$(curl ...)"
# expands the substitution before run is ever called, so a dry run would
# download the script and print the whole thing. A dry run that hits the
# network is not a dry run.
run_remote() {
  local url="$1"
  if [ "$DRY_RUN" = 1 ]; then
    printf '       %s$ /bin/bash -c "$(curl -fsSL %s)"%s\n' "$DIM" "$url" "$OFF"
    return 0
  fi
  /bin/bash -c "$(curl -fsSL "$url")"
}

# Same reasoning for anything piped through sudo tee.
run_sh() {
  if [ "$DRY_RUN" = 1 ]; then
    printf '       %s$ %s%s\n' "$DIM" "$1" "$OFF"
    return 0
  fi
  /bin/bash -c "$1"
}

FAILED=0
fail() { warn "$1"; FAILED=1; }

# The file a LOGIN shell actually reads. On Ubuntu, bash reads .bash_profile,
# then .bash_login, then .profile — the FIRST one that exists, and stops. Ubuntu
# ships .profile only, and that file is what adds ~/.local/bin to PATH and
# sources .bashrc. Creating a .bash_profile would shadow it and quietly break
# both. So: use .bash_profile only if the student already has one.
if [ -f "$HOME/.bash_profile" ]; then
  SHELL_PROFILE="$HOME/.bash_profile"
else
  SHELL_PROFILE="$HOME/.profile"
fi

# env -i is load-bearing. A login shell INHERITS PATH from its caller and adds
# to it; it does not rebuild it. So "$SHELL -lc ..." from inside this script
# would find tools purely because this script already put them on PATH, and
# would report success for a student whose next terminal cannot find anything.
LOGIN_SHELL="${SHELL:-/bin/bash}"
login_finds() {
  env -i HOME="$HOME" USER="${USER:-$(id -un)}" TERM="${TERM:-dumb}" \
    "$LOGIN_SHELL" -lc "command -v $1 >/dev/null 2>&1" >/dev/null 2>&1
}

ensure_on_path() {
  local dir="$1"
  if [ -f "$SHELL_PROFILE" ] && grep -qF "$dir" "$SHELL_PROFILE" 2>/dev/null; then
    return 0
  fi
  printf '\n# Added by the CMS 2026 setup script\nexport PATH="%s:$PATH"\n' "$dir" >> "$SHELL_PROFILE"
}

# ------------------------------------------------------------ preflight ----

printf '%sCMS 2026 setup (WSL)%s  %s(version %s)%s\n' "$B" "$OFF" "$DIM" "$SETUP_VERSION" "$OFF"

if [ "$(uname -s)" = "Darwin" ]; then
  echo "This is the Windows/WSL script. On a Mac, run setup.sh instead." >&2
  exit 1
fi

if ! grep -qiE "microsoft|wsl" /proc/version 2>/dev/null; then
  warn "This does not look like WSL."
  note "It may still work on plain Debian or Ubuntu. If you are on Windows and"
  note "saw this, you are probably in PowerShell rather than in your WSL"
  note "terminal — see WINDOWS.md."
  echo
fi

if ! command -v apt-get >/dev/null 2>&1; then
  echo "This script needs apt, so it expects Ubuntu or Debian." >&2
  echo "If you chose a different WSL distribution, tell us and we will help." >&2
  exit 1
fi

step "Checking what you already have"

command -v git    >/dev/null 2>&1 && have "git        $(git --version)"           || todo "git        not installed"
command -v gh     >/dev/null 2>&1 && have "gh         $(gh --version | head -1)"  || todo "gh         not installed"
command -v ffmpeg >/dev/null 2>&1 && have "ffmpeg     $(ffmpeg -version 2>/dev/null | head -1 | cut -d' ' -f1-3)" || todo "ffmpeg     not installed"
command -v claude >/dev/null 2>&1 && have "claude     $(claude --version)"        || todo "claude     not installed"

if [ "$CHECK_ONLY" = 1 ]; then
  printf '\n%sNothing was changed.%s Run without --check to install what is missing.\n' "$DIM" "$OFF"
  exit 0
fi

if [ "$DRY_RUN" = 1 ]; then
  printf '\n%sDry run. Nothing below will actually run.%s\n' "$YELLOW$B" "$OFF"
fi

# ------------------------------------------------------- apt and the CLI ----

step "Updating the package list"
note "sudo will ask for the password you chose when you set up Ubuntu."
run sudo apt-get update -qq || fail "apt-get update failed"

step "git and ffmpeg"
note "git tracks your work. ffmpeg handles video, and you will want it by Week 8."

for pkg in git ffmpeg; do
  if command -v "$pkg" >/dev/null 2>&1; then
    have "$pkg already installed"
  else
    todo "installing $pkg"
    run sudo apt-get install -y -qq "$pkg" || fail "apt-get install $pkg failed"
  fi
done

step "The GitHub CLI"
note "gh talks to GitHub, and signs git in so that pushing works."

if command -v gh >/dev/null 2>&1; then
  have "gh already installed"
else
  todo "adding GitHub's package repository, then installing"
  note "Ubuntu's own gh package is often well behind, so this uses GitHub's."
  run sudo mkdir -p -m 755 /etc/apt/keyrings
  run_sh 'curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | sudo tee /etc/apt/keyrings/githubcli-archive-keyring.gpg > /dev/null' \
    || fail "could not fetch GitHub's signing key"
  run sudo chmod go+r /etc/apt/keyrings/githubcli-archive-keyring.gpg
  run_sh 'echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | sudo tee /etc/apt/sources.list.d/github-cli.list > /dev/null' \
    || fail "could not add GitHub's package repository"
  run sudo apt-get update -qq
  run sudo apt-get install -y -qq gh || fail "apt-get install gh failed"
fi

# -------------------------------------------------------- claude code ----

step "Claude Code"
note "The terminal client. It signs in with the Claude Pro account you already bought."

if command -v claude >/dev/null 2>&1; then
  have "already installed ($(claude --version))"
  note "It updates itself in the background; there is nothing to do here."
else
  todo "installing"
  run_remote "https://claude.ai/install.sh" || fail "Claude Code install failed"
  export PATH="$HOME/.local/bin:$PATH"
fi

# ------------------------------------------------ connect gh to git ----

step "Connecting GitHub to git"
note "So that git push works without asking you for a password every time."

if [ "$DRY_RUN" = 1 ]; then
  printf '       %s$ gh auth setup-git%s\n' "$DIM" "$OFF"
  note "(only runs once you have signed in with gh auth login)"
elif ! command -v gh >/dev/null 2>&1; then
  todo "skipped — gh is not installed"
elif gh auth status >/dev/null 2>&1; then
  todo "you are signed in; wiring git up to use it"
  run gh auth setup-git && have "git will now use your GitHub sign-in" \
    || fail "gh auth setup-git failed"
else
  todo "not signed in yet — do this after gh auth login (see below)"
fi

# ------------------------------------------------------------- verify ----

step "Checking it all worked"

if [ "$DRY_RUN" = 1 ]; then
  note "Dry run — nothing was installed, so there is nothing to verify."
  exit 0
fi

# Ask a fresh login shell, not this one — see login_finds above.
for tool in git gh ffmpeg claude; do
  if login_finds "$tool"; then
    have "$tool"
  elif command -v "$tool" >/dev/null 2>&1; then
    todo "$tool works here but a new terminal would not find it — fixing"
    ensure_on_path "$(dirname "$(command -v "$tool")")"
    if login_finds "$tool"; then
      have "$tool (added to $(basename "$SHELL_PROFILE"))"
    else
      fail "$tool is installed but not on a new terminal's PATH, and the fix did not take"
    fi
  else
    fail "$tool is not installed"
  fi
done

printf '\n'
if [ "$FAILED" = 1 ]; then
  printf '%sSomething did not work.%s\n\n' "$RED$B" "$OFF"
  echo "Copy the exact error text above — do not retype it from memory, and do not"
  echo "summarise it. The precise wording is usually the whole answer. Send it to us,"
  echo "or bring it to class."
  exit 1
fi

printf '%sDone.%s\n\n' "$GREEN$B" "$OFF"
echo "Two things left, and neither is automatic:"
echo
echo "  1. Close this terminal and open a new one, so it picks up the changes."
echo
echo "  2. Sign in to GitHub, then let git use that sign-in:"
echo
echo "         gh auth login"
echo "         gh auth setup-git"
echo
echo "     Choose HTTPS, and authenticate in the browser when it offers. WSL will"
echo "     open your Windows browser; that is expected."
echo
echo "Then check everything is there:"
echo
echo "     git --version && gh --version && ffmpeg -version | head -1 && claude --version"
echo
echo "Four answers means you are ready."
