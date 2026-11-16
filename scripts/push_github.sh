#!/usr/bin/env bash
# Commit files to a GitHub repo and push straight to main (the user's own repos; he wants direct pushes to main).
#   TOKEN=<token from git_credentials mode=write> push_github.sh REPO MESSAGE LOCAL=REPOPATH [LOCAL=REPOPATH ...]
#   e.g. push_github.sh nadavcoh/masks-pwa "Update masks ..." /home/claude/work/index.html=index.html
#        push_github.sh nadavcoh/totm-mask-updater "msg" /tmp/totm-mask-updater=.      (a directory copies its contents)
# Env: DRY_RUN=1 -> clone, copy, show the diff, commit locally, but do not push (no TOKEN needed for a public repo).
# The token is only used through an http.extraheader, is never echoed, and is scrubbed from any output.
# Do not use `diff <(...)` in the bash tool: it runs /bin/sh. Use `bash -c` or `git diff --stat` instead.
set -euo pipefail
REPO="$1"; MSG="$2"; shift 2
WORK="/tmp/push_$(echo "$REPO" | tr '/' '_')"
rm -rf "$WORK"
TOKEN="${TOKEN:-}"
H=""
[ -n "$TOKEN" ] && H="Authorization: Basic $(printf 'x-access-token:%s' "$TOKEN" | base64 -w0)"
scrub() { if [ -n "$TOKEN" ]; then sed "s/$TOKEN/***/g"; else cat; fi; }
git -c credential.helper= ${H:+-c "http.extraheader=$H"} clone -q "https://github.com/$REPO.git" "$WORK" 2>&1 | scrub || true
cd "$WORK"
for pair in "$@"; do
  src="${pair%%=*}"; dst="${pair#*=}"
  if [ -d "$src" ]; then mkdir -p "$dst"; tar -C "$src" --exclude=.git --exclude=__pycache__ -cf - . | tar -C "$dst" -xf -
  else mkdir -p "$(dirname "$dst")"; cp "$src" "$dst"; fi
done
git add -A
git status --short
git diff --cached --stat | tail -5
if git diff --cached --quiet; then echo "nothing to commit"; exit 0; fi
git -c user.name="Claude" -c user.email="noreply@anthropic.com" commit -q -m "$MSG"
if [ "${DRY_RUN:-0}" = "1" ]; then echo "DRY RUN: committed locally in $WORK, not pushed"; exit 0; fi
[ -n "$TOKEN" ] || { echo "TOKEN not set" >&2; exit 1; }
git -c credential.helper= -c "http.extraheader=$H" push origin HEAD:refs/heads/main 2>&1 | scrub
echo "pushed: $(git log --oneline -1)"
