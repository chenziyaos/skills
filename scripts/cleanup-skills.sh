#!/usr/bin/env bash
set -euo pipefail

MANAGED_MARKER=".repo-skill-source"

usage() {
  cat <<'EOF'
Usage: cleanup-skills.sh [options] [skill-name ...]

Audit global Claude Code and Codex skill directories for repo-managed skills.
By default this script only reports state. Use --apply to remove stale repo-managed entries.

Options:
  --apply                    Remove stale repo-managed symlinks and stale repo-managed copies
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

path_is_within_repo() {
  local candidate
  candidate="$(realpath_safe "$1")"

  case "$candidate" in
    "$REPO_ROOT"|"$REPO_ROOT"/*) return 0 ;;
    *) return 1 ;;
  esac
}

assert_removable_path() {
  local target_path="$1"

  [[ -n "$target_path" ]] || die "refusing to remove an empty path"
  [[ "$target_path" != "/" ]] || die "refusing to remove /"

  case "$target_path" in
    "$CLAUDE_SKILLS_DIR"/*|"$CODEX_SKILLS_DIR"/*) ;;
    *) die "refusing to remove unmanaged path: $target_path" ;;
  esac
}

remove_path() {
  local target_path="$1"
  local reason="$2"

  assert_removable_path "$target_path"

  if [[ $APPLY -eq 1 ]]; then
    if [[ -L "$target_path" ]]; then
      rm "$target_path"
    else
      rm -rf "${target_path:?}"
    fi
    printf '[remove] %s (%s)\n' "$target_path" "$reason"
  else
    printf '[would-remove] %s (%s)\n' "$target_path" "$reason"
  fi
}

report_expected_target() {
  local source_dir="$1"
  local target_path="$2"
  local label="$3"
  local allow_copy="$4"

  if [[ -L "$target_path" ]]; then
    if [[ "$(realpath_safe "$target_path")" == "$(realpath_safe "$source_dir")" ]]; then
      printf '[ok] %s managed symlink: %s\n' "$label" "$target_path"
    elif path_is_within_repo "$target_path"; then
      printf '[warn] %s repo symlink points to another skill: %s\n' "$label" "$target_path"
    else
      printf '[warn] %s conflicts with another symlink: %s\n' "$label" "$target_path"
    fi
    return 0
  fi

  if [[ $allow_copy -eq 1 && -d "$target_path" && -f "$target_path/$MANAGED_MARKER" ]]; then
    marker_source="$(read_managed_marker "$target_path")"
    if [[ "$marker_source" == "$(realpath_safe "$source_dir")" ]]; then
      if compare_skill_tree "$source_dir" "$target_path"; then
        printf '[ok] %s managed copy: %s\n' "$label" "$target_path"
      else
        printf '[warn] %s managed copy drifted from source: %s\n' "$label" "$target_path"
      fi
    elif path_is_within_repo "$marker_source"; then
      printf '[warn] %s repo-managed copy points to another source: %s\n' "$label" "$target_path"
    else
      printf '[warn] %s copy is managed by another source: %s\n' "$label" "$target_path"
    fi
    return 0
  fi

  if [[ -e "$target_path" ]]; then
    printf '[warn] %s conflicts with existing path: %s\n' "$label" "$target_path"
  else
    printf '[info] %s target missing: %s\n' "$label" "$target_path"
  fi
}

scan_stale_entries() {
  local skills_dir="$1"
  local label="$2"
  local allow_copy="$3"
  local entry
  local entry_name
  local expected_source
  local marker_source

  [[ -d "$skills_dir" ]] || return 0

  while IFS= read -r entry; do
    entry_name="$(basename "$entry")"

    if [[ -L "$entry" ]]; then
      if ! path_is_within_repo "$entry"; then
        continue
      fi

      expected_source="$REPO_ROOT/$entry_name"
      if [[ ! -f "$expected_source/SKILL.md" ]]; then
        remove_path "$entry" "$label stale repo symlink"
      fi
      continue
    fi

    if [[ $allow_copy -eq 1 && -d "$entry" && -f "$entry/$MANAGED_MARKER" ]]; then
      marker_source="$(read_managed_marker "$entry")"
      if ! path_is_within_repo "$marker_source"; then
        continue
      fi

      expected_source="$REPO_ROOT/$entry_name"
      if [[ ! -f "$marker_source/SKILL.md" || ! -f "$expected_source/SKILL.md" || "$(realpath_safe "$expected_source")" != "$marker_source" ]]; then
        remove_path "$entry" "$label stale repo copy"
      fi
    fi
  done < <(find "$skills_dir" -mindepth 1 -maxdepth 1 \( -type d -o -type l \) | sort)
}

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd -- "$SCRIPT_DIR/.." && pwd)"
CLAUDE_SKILLS_DIR="${CLAUDE_SKILLS_DIR:-$HOME/.claude/skills}"
CODEX_SKILLS_DIR="${CODEX_SKILLS_DIR:-$HOME/.codex/skills}"
APPLY=0
REQUESTED_SKILLS=()

while [[ $# -gt 0 ]]; do
  case "$1" in
    --apply)
      APPLY=1
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

found_any=0

while IFS= read -r skill_manifest; do
  skill_dir="$(dirname "$skill_manifest")"
  skill_name="$(basename "$skill_dir")"

  if ! contains_requested_skill "$skill_name"; then
    continue
  fi

  found_any=1
  report_expected_target "$skill_dir" "$CLAUDE_SKILLS_DIR/$skill_name" "Claude" 0
  report_expected_target "$skill_dir" "$CODEX_SKILLS_DIR/$skill_name" "Codex" 1

done < <(find "$REPO_ROOT" -mindepth 2 -maxdepth 2 -type f -name 'SKILL.md' | sort)

if [[ $found_any -eq 0 && ${#REQUESTED_SKILLS[@]} -gt 0 ]]; then
  die "no matching skills found in repo: ${REQUESTED_SKILLS[*]}"
fi

if [[ ${#REQUESTED_SKILLS[@]} -eq 0 ]]; then
  scan_stale_entries "$CLAUDE_SKILLS_DIR" "Claude" 0
  scan_stale_entries "$CODEX_SKILLS_DIR" "Codex" 1
fi

if [[ $found_any -eq 0 && ${#REQUESTED_SKILLS[@]} -eq 0 ]]; then
  printf 'No skills found under %s\n' "$REPO_ROOT"
fi
