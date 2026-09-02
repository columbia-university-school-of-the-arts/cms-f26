#!/usr/bin/env bash
#
# Coding for Media Studies (CMS 2026) — toolchain setup, macOS.
#
# Installs, in order: Homebrew, git, GitHub CLI, Claude Code.
# Safe to run more than once. Anything already installed is reported and
# skipped rather than reinstalled.
#
#   ./setup.sh --dry-run    show every command without running any of them
#   ./setup.sh              do it
#   ./setup.sh --check      only report what is already present
#
# Windows is not supported yet. See README.
#
# This script asks for your password once, when Homebrew installs. That is
# Homebrew needing to create directories it does not yet own, not this script
# doing anything on its own account. If that makes you uneasy, good — run
# --dry-run first and read what it intends to do. You should extend that
# suspicion to every install script you are ever asked to pipe into a shell,
# including this one.

set -uo pipefail

# Bumped by hand. Printed on every run so that a stale copy is visible in the
# room rather than inferred from odd behaviour.
SETUP_VERSION="2026.09.02"

DRY_RUN=0
CHECK_ONLY=0
for arg in "$@"; do
  case "$arg" in
    --dry-run) DRY_RUN=1 ;;
    --check)   CHECK_ONLY=1 ;;
    -h|--help) sed -n '2,20p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
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

# Run a command, or print it under --dry-run. Never hides a failure.
run() {
  if [ "$DRY_RUN" = 1 ]; then
    printf '       %s$ %s%s\n' "$DIM" "$*" "$OFF"
    return 0
  fi
  "$@"
}

# Run a remote install script. The fetch MUST happen inside the guard: writing
# run /bin/bash -c "$(curl ...)" expands the substitution before run is ever
# called, so a dry run would download the script and print the whole thing. A
# dry run that hits the network is not a dry run.
run_remote() {
  local url="$1"
  if [ "$DRY_RUN" = 1 ]; then
    printf '       %s$ /bin/bash -c "$(curl -fsSL %s)"%s\n' "$DIM" "$url" "$OFF"
    return 0
  fi
  /bin/bash -c "$(curl -fsSL "$url")"
}

FAILED=0
fail() { warn "$1"; FAILED=1; }

# ------------------------------------------------------------ preflight ----

if [ "$(uname -s)" != "Darwin" ]; then
  echo "This is the macOS script." >&2
  echo >&2
  if grep -qiE "microsoft|wsl" /proc/version 2>/dev/null; then
    echo "You are in WSL — run ./setup-wsl.sh instead." >&2
  else
    echo "On Windows, install WSL first (see WINDOWS.md), then run setup-wsl.sh" >&2
    echo "inside it." >&2
  fi
  exit 1
fi

printf '%sCMS 2026 setup%s  %s(version %s)%s\n' "$B" "$OFF" "$DIM" "$SETUP_VERSION" "$OFF"

step "Checking what you already have"

BREW_BIN=""
for candidate in /opt/homebrew/bin/brew /usr/local/bin/brew; do
  [ -x "$candidate" ] && { BREW_BIN="$candidate"; break; }
done
command -v brew >/dev/null 2>&1 && BREW_BIN="$(command -v brew)"

[ -n "$BREW_BIN" ] && have "Homebrew   $("$BREW_BIN" --version 2>/dev/null | head -1)" \
                   || todo "Homebrew   not installed"
command -v git    >/dev/null 2>&1 && have "git        $(git --version)"    || todo "git        not installed"
command -v gh     >/dev/null 2>&1 && have "gh         $(gh --version | head -1)" || todo "gh         not installed"
command -v claude >/dev/null 2>&1 && have "claude     $(claude --version)" || todo "claude     not installed"

if [ "$CHECK_ONLY" = 1 ]; then
  printf '\n%sNothing was changed.%s Run without --check to install what is missing.\n' "$DIM" "$OFF"
  exit 0
fi

if [ "$DRY_RUN" = 1 ]; then
  printf '\n%sDry run. Nothing below will actually run.%s\n' "$YELLOW$B" "$OFF"
fi

# ------------------------------------------------------------- homebrew ----

step "Homebrew"
note "The package manager. git and gh are installed through it."

if [ -n "$BREW_BIN" ]; then
  have "already installed at $BREW_BIN"
else
  todo "installing — this is the slow one, and it will ask for your password"
  run_remote "https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh" \
    || fail "Homebrew install failed. Nothing after this will work; fix it first."

  for candidate in /opt/homebrew/bin/brew /usr/local/bin/brew; do
    [ -x "$candidate" ] && { BREW_BIN="$candidate"; break; }
  done
fi

# Put brew on PATH for the rest of this script, and for future shells.
if [ -n "$BREW_BIN" ] && [ "$DRY_RUN" = 0 ]; then
  eval "$("$BREW_BIN" shellenv)"
fi

if [ -n "$BREW_BIN" ]; then
  SHELL_PROFILE="$HOME/.zprofile"
  [ "$(basename "${SHELL:-/bin/zsh}")" = "bash" ] && SHELL_PROFILE="$HOME/.bash_profile"
  SHELLENV_LINE="eval \"\$($BREW_BIN shellenv)\""
  if [ -f "$SHELL_PROFILE" ] && grep -qF "$BREW_BIN shellenv" "$SHELL_PROFILE" 2>/dev/null; then
    have "already on your PATH in $(basename "$SHELL_PROFILE")"
  else
    todo "adding to $(basename "$SHELL_PROFILE") so new terminals find it"
    if [ "$DRY_RUN" = 1 ]; then
      printf '       %s$ echo %s >> %s%s\n' "$DIM" "'$SHELLENV_LINE'" "$SHELL_PROFILE" "$OFF"
    else
      printf '\n# Homebrew (added by the CMS 2026 setup script)\n%s\n' "$SHELLENV_LINE" >> "$SHELL_PROFILE"
    fi
  fi
fi

# ---------------------------------------------------------- git and gh ----

step "git and the GitHub CLI"
note "git tracks your work. gh talks to GitHub, and signs you in so you can push."

for pkg in git gh; do
  if command -v "$pkg" >/dev/null 2>&1 && [ -n "${BREW_BIN:-}" ] && \
     "$BREW_BIN" list --formula "$pkg" >/dev/null 2>&1; then
    have "$pkg already installed by Homebrew"
  elif command -v "$pkg" >/dev/null 2>&1 && [ "$pkg" = "git" ]; then
    have "git already present ($(git --version)) — leaving it alone"
    note "macOS ships an older git with the developer tools. That is fine for this course."
  else
    todo "installing $pkg"
    run "$BREW_BIN" install "$pkg" || fail "brew install $pkg failed"
  fi
done

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

for tool in brew git gh claude; do
  if command -v "$tool" >/dev/null 2>&1; then
    have "$tool"
  else
    fail "$tool is still not on your PATH"
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
echo "     Choose HTTPS, and authenticate in the browser when it offers."
echo "     The second command is what lets you push without a password later."
echo
echo "Then check everything is there:"
echo
echo "     brew --version && git --version && gh --version && claude --version"
echo
echo "Four version numbers means you are ready."
