#!/usr/bin/env bash
# Report whether a TMDB token is configured and accepted, without ever
# printing it. Looks in the shell environment first, then ./.env.
# Prints one of: MISSING, EMPTY, REJECTED, OK, UNREACHABLE.
set -u
token="${TMDB_TOKEN:-}"
if [ -z "$token" ] && [ -f .env ]; then
  token="$(grep -m1 '^TMDB_TOKEN=' .env | cut -d= -f2- | tr -d '"'"'"' \r')"
  grep -q '^TMDB_TOKEN=' .env || { echo MISSING; exit 1; }
fi
[ -z "$token" ] && { [ -f .env ] && echo EMPTY || echo MISSING; exit 1; }
code="$(curl -s -o /dev/null -w '%{http_code}' --max-time 15 \
  -H "Authorization: Bearer $token" https://api.themoviedb.org/3/authentication)" || true
case "$code" in
  200) echo OK ;;
  401) echo REJECTED; exit 2 ;;
  000|"") echo UNREACHABLE; exit 3 ;;
  *) echo "UNEXPECTED_$code"; exit 3 ;;
esac
