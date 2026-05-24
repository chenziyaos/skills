#!/usr/bin/env bash
set -euo pipefail

MANAGED_MARKER=".repo-skill-source"

usage() {
  cat <<'EOF'
Usage: verify-skills.sh [options] [skill-name ...]

Verify repo skills are installed in Claude Code and Codex global skill directories.

Options:
  --allow-codex-copy         Accept a copied Codex skill directory instead of a symlink
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

compare_skill_tree() {
  local source_dir="$1"
  local target_path="$2"

  diff -qr -x "$MANAGED_MARKER" "$source_dir" "$target_path" >/dev/null
}

contains_requested_skill() {
  local skill_name="$1"

  if [[ ${#REQUESTED_SKILLS[@]} -eq 0 ]]; then
    return 0
  fi

  local requested
  for requested in "${REQUESTED_SKILLS[@]}"; do
    if [[ "$requested" == "$skill_name" ]]; then
      return 0
    fi
  done

  return 1
}

verify_symlink_target() {
  local source_dir="$1"
  local target_path="$2"
  local label="$3"

  if [[ ! -L "$target_path" ]]; then
    printf '[fail] %s is not a symlink: %s\n' "$label" "$target_path" >&2
    return 1
  fi

  if [[ "$(realpath_safe "$target_path")" != "$(realpath_safe "$source_dir")" ]]; then
    printf '[fail] %s points elsewhere: %s\n' "$label" "$target_path" >&2
    return 1
  fi

  if [[ ! -f "$target_path/SKILL.md" ]]; then
    printf '[fail] %s is missing SKILL.md: %s\n' "$label" "$target_path" >&2
    return 1
  fi

  printf '[ok] %s symlink verified: %s\n' "$label" "$target_path"
  return 0
}

verify_directory_copy() {
  local source_dir="$1"
  local target_path="$2"
  local label="$3"

  if [[ ! -d "$target_path" ]]; then
    printf '[fail] %s is missing directory: %s\n' "$label" "$target_path" >&2
    return 1
  fi

  if [[ ! -f "$target_path/SKILL.md" ]]; then
    printf '[fail] %s is missing SKILL.md: %s\n' "$label" "$target_path" >&2
    return 1
  fi

  if [[ ! -f "$target_path/$MANAGED_MARKER" ]]; then
    printf '[fail] %s copy is missing marker: %s\n' "$label" "$target_path" >&2
    return 1
  fi

  if [[ "$(read_managed_marker "$target_path")" != "$(realpath_safe "$source_dir")" ]]; then
    printf '[fail] %s copy marker points elsewhere: %s\n' "$label" "$target_path" >&2
    return 1
  fi

  if ! compare_skill_tree "$source_dir" "$target_path"; then
    printf '[fail] %s directory differs from source: %s\n' "$label" "$target_path" >&2
    return 1
  fi

  printf '[ok] %s copied directory verified: %s\n' "$label" "$target_path"
  return 0
}

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd -- "$SCRIPT_DIR/.." && pwd)"
CLAUDE_SKILLS_DIR="${CLAUDE_SKILLS_DIR:-$HOME/.claude/skills}"
CODEX_SKILLS_DIR="${CODEX_SKILLS_DIR:-$HOME/.codex/skills}"
ALLOW_CODEX_COPY=0
REQUESTED_SKILLS=()

while [[ $# -gt 0 ]]; do
  case "$1" in
    --allow-codex-copy)
      ALLOW_CODEX_COPY=1
      ;;
    --help|-h)
      usage
      exit 0
      ;;
    *)
      REQUESTED_SKILLS+=("$1")
      ;;
  esac
  shift
done

failures=0
found_any=0

while IFS= read -r skill_manifest; do
  skill_dir="$(dirname "$skill_manifest")"
  skill_name="$(basename "$skill_dir")"

  if ! contains_requested_skill "$skill_name"; then
    continue
  fi

  found_any=1

  if ! verify_symlink_target "$skill_dir" "$CLAUDE_SKILLS_DIR/$skill_name" "Claude"; then
    failures=$((failures + 1))
  fi

  if [[ -L "$CODEX_SKILLS_DIR/$skill_name" ]]; then
    if ! verify_symlink_target "$skill_dir" "$CODEX_SKILLS_DIR/$skill_name" "Codex"; then
      failures=$((failures + 1))
    fi
  elif [[ $ALLOW_CODEX_COPY -eq 1 ]]; then
    if ! verify_directory_copy "$skill_dir" "$CODEX_SKILLS_DIR/$skill_name" "Codex"; then
      failures=$((failures + 1))
    fi
  else
    printf '[fail] Codex is not a symlink: %s\n' "$CODEX_SKILLS_DIR/$skill_name" >&2
    failures=$((failures + 1))
  fi

done < <(find "$REPO_ROOT" -mindepth 2 -maxdepth 2 -type f -name 'SKILL.md' | sort)

if [[ $found_any -eq 0 && ${#REQUESTED_SKILLS[@]} -gt 0 ]]; then
  die "no matching skills found in repo: ${REQUESTED_SKILLS[*]}"
fi

if [[ $found_any -eq 0 ]]; then
  die "no skills found under $REPO_ROOT"
fi

if [[ $failures -gt 0 ]]; then
  exit 1
fi

printf 'Verification passed for %s\n' "${REQUESTED_SKILLS[*]:-all repo skills}"
