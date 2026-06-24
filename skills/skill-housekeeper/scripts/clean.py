#!/usr/bin/env python3
"""clean.py — GC the local skill workspace's meta-skill state directories.

Behavior:
  - Default: dry-run report only. Lists what *would* be archived / truncated.
  - --apply: actually move stale items to <state>/_archive/<run-date>/.
  - --apply --hard-delete: actually `rm` archived items (still bounded to _archive/).
  - Never touches SKILL.md, references/, scripts/, byted/, or anything outside this repo.

Scope (hard-coded):
  self/skills/workflow-packager/.workflow-packager/
  self/skills/skill-refiner/.skill-refiner/

Doctrine: see references/housekeeping-rules.md.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import shutil
import sys
from dataclasses import dataclass, field
from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parent.parent
REPO_ROOT = SKILL_DIR.parent.parent.parent
CONFIG_FILE = REPO_ROOT / "skills.config.json"

WORKSPACES = [
    {
        "name": "workflow-packager",
        "state_dir": REPO_ROOT / "self" / "skills" / "workflow-packager" / ".workflow-packager",
    },
    {
        "name": "skill-refiner",
        "state_dir": REPO_ROOT / "self" / "skills" / "skill-refiner" / ".skill-refiner",
    },
]

CANDIDATE_FILE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}\.md$")
SNAPSHOT_FILE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}\.json$")
LEGACY_AUDIT_SNAPSHOT_RE = re.compile(r"^audit-\d{4}-\d{2}-\d{2}\.json$")
WATCH_TABLE_ROW_RE = re.compile(r"^\|\s*(?!signature|---)([^|]+)\|\s*(\d+)\s*\|")


@dataclass
class Action:
    kind: str             # "archive" | "truncate" | "warn" | "drop-archive"
    workspace: str
    path: Path
    reason: str
    bytes_freed: int = 0
    detail: str = ""


@dataclass
class Report:
    actions: list[Action] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)

    def total_bytes(self) -> int:
        return sum(a.bytes_freed for a in self.actions if a.kind != "warn")


# ---------- safety ----------

def safety_check_or_die() -> None:
    if not CONFIG_FILE.is_file():
        sys.stderr.write(
            f"refusing to run: {CONFIG_FILE} not found — am I really inside aiops/skills?\n"
        )
        sys.exit(2)
    try:
        json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        sys.stderr.write(f"refusing to run: {CONFIG_FILE} is not valid JSON: {e}\n")
        sys.exit(2)


def assert_inside_repo(p: Path) -> None:
    try:
        p.resolve().relative_to(REPO_ROOT.resolve())
    except ValueError:
        sys.stderr.write(f"refusing to operate outside repo root: {p}\n")
        sys.exit(2)


SKILL_PROTECTED_NAMES = {"SKILL.md", "references", "scripts", "tests"}


def assert_not_protected(p: Path) -> None:
    parts = p.resolve().parts
    if any(part in SKILL_PROTECTED_NAMES for part in parts):
        # The .state/_archive/<date>/<filename> could include "references" by chance;
        # check more carefully: refuse if any *directory ancestor* is one of these.
        # Files literally named SKILL.md anywhere are always refused.
        if p.name == "SKILL.md":
            sys.stderr.write(f"refusing to touch SKILL.md: {p}\n")
            sys.exit(2)
        # references / scripts / tests as parent dir name
        for parent in p.resolve().parents:
            if parent.name in {"references", "scripts", "tests"}:
                # only protect when parent is *inside a skill source*, not inside .state/
                if not any(part.startswith(".") for part in parent.parts):
                    sys.stderr.write(f"refusing to touch protected dir: {p} (parent={parent})\n")
                    sys.exit(2)


# ---------- scan ----------

def scan_candidate_reports(ws_name: str, state_dir: Path, keep: int, report: Report) -> None:
    cdir = state_dir / "candidates"
    if not cdir.is_dir():
        return
    files = sorted(
        [p for p in cdir.iterdir() if p.is_file() and CANDIDATE_FILE_RE.match(p.name)],
        reverse=True,  # newest first by name (date)
    )
    if len(files) <= keep:
        return
    for old in files[keep:]:
        sz = old.stat().st_size
        report.actions.append(Action(
            kind="archive",
            workspace=ws_name,
            path=old,
            reason=f"older than the {keep} most-recent candidate reports",
            bytes_freed=sz,
            detail=f"{sz} bytes, mtime={dt.date.fromtimestamp(old.stat().st_mtime).isoformat()}",
        ))


def scan_audit_snapshots(ws_name: str, state_dir: Path, keep: int, report: Report) -> None:
    snapshots_dir = state_dir / "snapshots"
    if snapshots_dir.is_dir():
        snaps = sorted(
            [p for p in snapshots_dir.iterdir() if p.is_file() and SNAPSHOT_FILE_RE.match(p.name)],
            reverse=True,
        )
    else:
        snaps = sorted(
            [p for p in state_dir.iterdir() if p.is_file() and LEGACY_AUDIT_SNAPSHOT_RE.match(p.name)],
            reverse=True,
        )
    if len(snaps) <= keep:
        return
    for old in snaps[keep:]:
        sz = old.stat().st_size
        report.actions.append(Action(
            kind="archive",
            workspace=ws_name,
            path=old,
            reason=f"older than the {keep} most-recent audit snapshots",
            bytes_freed=sz,
            detail=f"{sz} bytes",
        ))


def scan_watch_file(ws_name: str, state_dir: Path, max_rows: int, report: Report) -> None:
    watch = state_dir / "watch.md"
    if not watch.is_file():
        return
    lines = watch.read_text(encoding="utf-8", errors="replace").splitlines()
    rows: list[tuple[int, str, int]] = []  # (line_idx, line, hits)
    for i, line in enumerate(lines):
        m = WATCH_TABLE_ROW_RE.match(line)
        if m:
            try:
                hits = int(m.group(2))
            except ValueError:
                continue
            rows.append((i, line, hits))
    if len(rows) <= max_rows:
        return
    rows_sorted = sorted(rows, key=lambda r: -r[2])
    keep_indices = {r[0] for r in rows_sorted[:max_rows]}
    drop_count = len(rows) - len(keep_indices)
    dropped_bytes = sum(len(r[1].encode("utf-8")) + 1 for r in rows if r[0] not in keep_indices)
    report.actions.append(Action(
        kind="truncate",
        workspace=ws_name,
        path=watch,
        reason=f"watch.md has {len(rows)} rows; would keep top-{max_rows} by hits",
        bytes_freed=dropped_bytes,
        detail=f"drop {drop_count} rows",
    ))


def scan_state_size(ws_name: str, state_dir: Path, warn_bytes: int, report: Report) -> None:
    total = 0
    for p in state_dir.rglob("*"):
        if p.is_file():
            try:
                total += p.stat().st_size
            except OSError:
                pass
    if total > warn_bytes:
        report.warnings.append(
            f"{ws_name}: .state/ is {total/1024/1024:.1f} MB (> {warn_bytes/1024/1024:.0f} MB warn threshold)"
        )


def scan_archive_rotation(ws_name: str, state_dir: Path, keep_runs: int, report: Report) -> None:
    archive = state_dir / "_archive"
    if not archive.is_dir():
        return
    # housekeeping run dirs look like YYYY-MM-DD-housekeeping
    run_dirs = sorted(
        [p for p in archive.iterdir() if p.is_dir() and p.name.endswith("-housekeeping")],
        reverse=True,
    )
    if len(run_dirs) <= keep_runs:
        return
    for old in run_dirs[keep_runs:]:
        sz = sum(p.stat().st_size for p in old.rglob("*") if p.is_file())
        report.actions.append(Action(
            kind="drop-archive",
            workspace=ws_name,
            path=old,
            reason=f"older than the {keep_runs} most-recent housekeeping runs in _archive/",
            bytes_freed=sz,
            detail=f"{sz} bytes",
        ))


# ---------- apply ----------

def apply_archive(action: Action, run_date: str, *, hard_delete: bool) -> None:
    assert_inside_repo(action.path)
    assert_not_protected(action.path)
    ws_state_dir = action.path.parent
    # walk up to .state dir (the one named .workflow-packager / .skill-refiner)
    while ws_state_dir.name not in {".workflow-packager", ".skill-refiner"} and ws_state_dir != REPO_ROOT:
        ws_state_dir = ws_state_dir.parent
    if ws_state_dir == REPO_ROOT:
        sys.stderr.write(f"could not locate state root for {action.path}; skipping\n")
        return
    archive_root = ws_state_dir / "_archive" / f"{run_date}-housekeeping"
    archive_root.mkdir(parents=True, exist_ok=True)
    dest = archive_root / action.path.name
    # ensure no clobber
    if dest.exists():
        dest = archive_root / f"{action.path.stem}.{int(action.path.stat().st_mtime)}{action.path.suffix}"
    shutil.move(str(action.path), str(dest))


def apply_truncate_watch(action: Action, max_rows: int) -> None:
    watch = action.path
    assert_inside_repo(watch)
    text = watch.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines()
    rows: list[tuple[int, str, int]] = []
    for i, line in enumerate(lines):
        m = WATCH_TABLE_ROW_RE.match(line)
        if m:
            try:
                rows.append((i, line, int(m.group(2))))
            except ValueError:
                pass
    if len(rows) <= max_rows:
        return
    rows_sorted = sorted(rows, key=lambda r: -r[2])
    keep_indices = {r[0] for r in rows_sorted[:max_rows]}
    dropped_rows = [r[1] for r in rows if r[0] not in keep_indices]

    archive_dir = watch.parent / "_archive"
    archive_dir.mkdir(parents=True, exist_ok=True)
    bak = archive_dir / f"watch-{dt.date.today().isoformat()}.md"
    bak.write_text(
        "# Watch rows truncated by skill-housekeeper\n\n"
        + "\n".join(dropped_rows) + "\n",
        encoding="utf-8",
    )

    new_lines = [line for i, line in enumerate(lines) if i not in {r[0] for r in rows} or i in keep_indices]
    watch.write_text("\n".join(new_lines) + "\n", encoding="utf-8")


def apply_drop_archive(action: Action, *, hard_delete: bool) -> None:
    assert_inside_repo(action.path)
    # safety: only inside an _archive dir
    parts = action.path.resolve().parts
    if "_archive" not in parts:
        sys.stderr.write(f"refusing to drop {action.path}: not under _archive/\n")
        return
    if not hard_delete:
        # without --hard-delete, leave drop-archive items alone (they're already archived)
        return
    if action.path.is_dir():
        shutil.rmtree(action.path)
    else:
        action.path.unlink()


# ---------- main ----------

def render_report(report: Report, *, applied: bool) -> str:
    out = []
    today = dt.date.today().isoformat()
    verb = "ARCHIVED" if applied else "WOULD ARCHIVE"
    out.append(f"# skill-housekeeper report ({today})\n")
    out.append(f"Scanned: {', '.join(w['name'] for w in WORKSPACES)}\n")

    if not report.actions and not report.warnings:
        out.append("\nNothing to clean. State directories are within thresholds.\n")
        return "\n".join(out)

    by_ws: dict[str, list[Action]] = {}
    for a in report.actions:
        by_ws.setdefault(a.workspace, []).append(a)

    for ws, actions in by_ws.items():
        out.append(f"\n## {ws}\n")
        for a in actions:
            tag = {
                "archive": verb,
                "truncate": "TRUNCATED" if applied else "WOULD TRUNCATE",
                "drop-archive": ("HARD-DELETED" if applied else "WOULD HARD-DELETE (--hard-delete required)"),
                "warn": "WARN",
            }[a.kind]
            rel = a.path.resolve().relative_to(REPO_ROOT.resolve())
            out.append(f"- [{tag}] `{rel}` — {a.reason}")
            if a.detail:
                out.append(f"    {a.detail}")
        sub = sum(x.bytes_freed for x in actions)
        out.append(f"  _subtotal: {sub} bytes_")

    if report.warnings:
        out.append("\n## Warnings (no action taken)\n")
        for w in report.warnings:
            out.append(f"- {w}")

    out.append(f"\n**total bytes {'freed' if applied else 'would free'}: {report.total_bytes()}**\n")
    out.append("\n## Next steps\n")
    if not applied:
        out.append("- Review the list above; re-run with `--apply` to archive items into `<state>/_archive/<date>-housekeeping/`.")
        out.append("- Add `--hard-delete` if you also want to remove old `_archive/<date>-housekeeping/` runs that exceed `--keep-archive-runs`.")
        out.append("- Use `--keep-candidates N` / `--keep-audits N` / `--watch-max-rows N` to tune.")
    else:
        out.append("- `./skillctl audit` — confirm SKILL.md files unaffected.")
        out.append("- `./skillctl verify` — confirm symlinks healthy.")
    return "\n".join(out)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true", help="actually perform archive/truncate (default is dry-run report)")
    parser.add_argument("--hard-delete", action="store_true", help="also drop _archive/ runs beyond --keep-archive-runs (only with --apply)")
    parser.add_argument("--keep-candidates", type=int, default=5, help="how many most-recent candidate reports to keep per workspace (default 5)")
    parser.add_argument("--keep-audits", type=int, default=4, help="how many most-recent audit snapshots to keep (default 4)")
    parser.add_argument("--keep-archive-runs", type=int, default=6, help="how many most-recent housekeeping run dirs to keep in _archive/ (default 6)")
    parser.add_argument("--watch-max-rows", type=int, default=50, help="max rows to keep in watch.md, sorted by hits desc (default 50)")
    parser.add_argument("--warn-bytes", type=int, default=50 * 1024 * 1024, help=".state/ size warn threshold in bytes (default 50 MB)")
    args = parser.parse_args()

    safety_check_or_die()
    report = Report()
    today = dt.date.today().isoformat()

    for ws in WORKSPACES:
        state_dir = ws["state_dir"]
        if not state_dir.is_dir():
            report.skipped.append(f"{ws['name']}: state dir not found ({state_dir})")
            continue
        scan_candidate_reports(ws["name"], state_dir, args.keep_candidates, report)
        scan_audit_snapshots(ws["name"], state_dir, args.keep_audits, report)
        scan_watch_file(ws["name"], state_dir, args.watch_max_rows, report)
        scan_state_size(ws["name"], state_dir, args.warn_bytes, report)
        scan_archive_rotation(ws["name"], state_dir, args.keep_archive_runs, report)

    if args.apply:
        for a in report.actions:
            if a.kind == "archive":
                apply_archive(a, today, hard_delete=args.hard_delete)
            elif a.kind == "truncate":
                apply_truncate_watch(a, args.watch_max_rows)
            elif a.kind == "drop-archive":
                apply_drop_archive(a, hard_delete=args.hard_delete)

    print(render_report(report, applied=args.apply))
    return 0


if __name__ == "__main__":
    sys.exit(main())
