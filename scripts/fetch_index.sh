#!/usr/bin/env bash
# Fetch the live mask-tracker page from GitHub so the user never has to upload index.html.
#   fetch_index.sh [DEST=/home/claude/work/index.html] [REPO=nadavcoh/masks-pwa] [BRANCH=main]
# The repo is public: plain curl on raw.githubusercontent.com works (github.com and
# raw.githubusercontent.com are on the sandbox allow-list). If it ever becomes private, get a
# read token with the gh-push-mcp git_credentials tool (mode=read) and clone with an http.extraheader.
set -euo pipefail
DEST="${1:-/home/claude/work/index.html}"
REPO="${2:-nadavcoh/masks-pwa}"
BRANCH="${3:-main}"
mkdir -p "$(dirname "$DEST")"
code=$(curl -sL -o "$DEST" -w '%{http_code}' "https://raw.githubusercontent.com/$REPO/$BRANCH/index.html")
[ "$code" = "200" ] || { echo "fetch failed: HTTP $code" >&2; exit 1; }
grep -q "const MASKS = \[" "$DEST" || { echo "WARNING: no 'const MASKS = [' block -> legacy page, run migrate_legacy.py first" >&2; }
echo "fetched $REPO@$BRANCH index.html -> $DEST ($(wc -c < "$DEST") bytes)"
