#!/usr/bin/env bash
set -euo pipefail

MANAGED_MARKER=".repo-skill-source"

usage() {
  cat <<'EOF'
Usage: list-skills.sh [options]

List repo skills and show whether they are installed for Claude Code and Codex.

Options:
  --help                     Show this help message

Environment:
  CLAUDE_SKILLS_DIR          Override Claude global skills directory
  CODEX_SKILLS_DIR           Override Codex global skills directory
EOF
}

die() {
  printf 'Error: %s\n' "$*" >&2
  exit 1
}

realpath_safe() {
  python3 -c 'import os, sys; print(os.path.realpath(sys.argv[1]))' "$1"
}

read_managed_marker() {
  local target_path="$1"
  local marker_path="$target_path/$MANAGED_MARKER"

  [[ -f "$marker_path" ]] || return 1

  python3 - "$marker_path" <<'PY'
import os
import sys

with open(sys.argv[1], 'r', encoding='utf-8') as handle:
    print(os.path.realpath(handle.read().strip()))
PY
}

path_is_same_source() {
  local source_dir="$1"
  local target_path="$2"

  [[ -e "$target_path" || -L "$target_path" ]] || return 1
  [[ "$(realpath_safe "$source_dir")" == "$(realpath_safe "$target_path")" ]]
}

status_for_target() {
  local source_dir="$1"
  local target_path="$2"
  local allow_copy="$3"

  if [[ -L "$target_path" ]]; then
    if path_is_same_source "$source_dir" "$target_path"; then
      printf 'symlink'
    else
      printf 'conflict'
    fi
    return 0
  fi

  if [[ $allow_copy -eq 1 && -d "$target_path" && -f "$target_path/$MANAGED_MARKER" ]]; then
    if [[ "$(read_managed_marker "$target_path")" == "$(realpath_safe "$source_dir")" ]]; then
      printf 'copy'
    else
      printf 'conflict'
    fi
    return 0
  fi

  if [[ -e "$target_path" ]]; then
    printf 'conflict'
  else
    printf 'missing'
  fi
}

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd -- "$SCRIPT_DIR/.." && pwd)"
CLAUDE_SKILLS_DIR="${CLAUDE_SKILLS_DIR:-$HOME/.claude/skills}"
CODEX_SKILLS_DIR="${CODEX_SKILLS_DIR:-$HOME/.codex/skills}"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --help|-h)
      usage
      exit 0
      ;;
    *)
      die "unsupported argument: $1"
      ;;
  esac
  shift
done

printf '%-24s %-10s %-10s %s\n' 'SKILL' 'CLAUDE' 'CODEX' 'SOURCE'
printf '%-24s %-10s %-10s %s\n' '-----' '------' '-----' '------'

found_any=0

while IFS= read -r skill_manifest; do
  skill_dir="$(dirname "$skill_manifest")"
  skill_name="$(basename "$skill_dir")"
  found_any=1

  claude_status="$(status_for_target "$skill_dir" "$CLAUDE_SKILLS_DIR/$skill_name" 0)"
  codex_status="$(status_for_target "$skill_dir" "$CODEX_SKILLS_DIR/$skill_name" 1)"

  printf '%-24s %-10s %-10s %s\n' "$skill_name" "$claude_status" "$codex_status" "$skill_dir"
done < <(find "$REPO_ROOT" -mindepth 2 -maxdepth 2 -type f -name 'SKILL.md' | sort)

if [[ $found_any -eq 0 ]]; then
  printf 'No skills found under %s\n' "$REPO_ROOT"
fi
