#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage: scripts/install.sh [--codex|--claude|--both] [repository]

Copies this skill into the selected repository-local skill directories.
Default mode: --both
Default repository: current directory
USAGE
}

mode="both"
if [[ ${1:-} == "--codex" || ${1:-} == "--claude" || ${1:-} == "--both" ]]; then
  mode="${1#--}"
  shift
elif [[ ${1:-} == "-h" || ${1:-} == "--help" ]]; then
  usage
  exit 0
fi

repo="${1:-.}"
repo="$(cd "$repo" && pwd)"
skill_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

copy_skill() {
  local base="$1"
  local dest="$repo/$base/normative-promises"
  mkdir -p "$(dirname "$dest")"
  rm -rf "$dest"
  cp -R "$skill_root" "$dest"
  echo "Installed $dest"
}

case "$mode" in
  codex) copy_skill ".agents/skills" ;;
  claude) copy_skill ".claude/skills" ;;
  both)
    copy_skill ".agents/skills"
    copy_skill ".claude/skills"
    ;;
  *) usage; exit 2 ;;
esac
