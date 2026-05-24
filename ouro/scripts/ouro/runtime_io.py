"""Runtime IO helpers for the Ouro shadow runtime."""
from __future__ import annotations

import argparse
import json
import shutil
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

from .artifacts import dump_governance_yaml, governance_artifact_payload
from .inventory import normalize_assets, parse_minimal_yaml
from .text_utils import safe_slug

DEFAULT_OUTPUT_ROOT = Path.home() / ".cache" / "ouro"
FALLBACK_OUTPUT_ROOT = Path("/tmp") / "ouro"
DEFAULT_CACHE_TTL_HOURS = 168
MAX_REPORTED_REMOVED_RUN_DIRS = 20


@dataclass(frozen=True)
class CleanupSummary:
    """Best-effort cleanup result for managed output roots."""

    removed_count: int
    removed_sample: tuple[str, ...]
    warnings: tuple[str, ...] = ()


def default_output_dir(run_id: str, *, output_root: Path = DEFAULT_OUTPUT_ROOT) -> Path:
    """Return the default per-run output directory."""
    return output_root / f"shadow_run_{run_id}"


def fallback_output_dir(run_id: str, *, output_root: Path = FALLBACK_OUTPUT_ROOT) -> Path:
    """Return a temp-backed fallback directory for constrained environments."""
    return output_root / f"shadow_run_{run_id}"


def cleanup_expired_output_dirs(
    root: Path,
    now: datetime,
    ttl_hours: int,
    exclude_names: set[str] | None = None,
    *,
    max_reported_removed_run_dirs: int = MAX_REPORTED_REMOVED_RUN_DIRS,
) -> CleanupSummary:
    """Remove expired shadow output directories under the managed cache root."""
    if ttl_hours < 0 or not root.exists():
        return CleanupSummary(removed_count=0, removed_sample=())
    excluded = exclude_names or set()
    cutoff = now.timestamp() - (ttl_hours * 3600)
    removed_count = 0
    removed_sample: list[str] = []
    warnings: list[str] = []
    for entry in root.iterdir():
        if entry.name in excluded or not entry.is_dir() or not entry.name.startswith("shadow_run_"):
            continue
        try:
            modified_at = entry.stat().st_mtime
        except OSError as exc:
            warnings.append(f"cleanup_stat_failed:{entry.name}:{exc}")
            continue
        if modified_at >= cutoff:
            continue
        try:
            shutil.rmtree(entry, ignore_errors=False)
        except OSError as exc:
            warnings.append(f"cleanup_remove_failed:{entry.name}:{exc}")
            continue
        removed_count += 1
        if len(removed_sample) < max_reported_removed_run_dirs:
            removed_sample.append(entry.name)
    return CleanupSummary(
        removed_count=removed_count,
        removed_sample=tuple(removed_sample),
        warnings=tuple(warnings),
    )


def ensure_output_dir(
    path: str | None,
    run_id: str,
    *,
    default_output_dir_fn: Callable[[str], Path] = default_output_dir,
    fallback_output_dir_fn: Callable[[str], Path] = fallback_output_dir,
    runtime_error_cls: type[Exception] = RuntimeError,
) -> tuple[Path, str]:
    """Create and return the requested output directory plus output mode."""
    if path:
        output_dir = Path(path).expanduser()
        try:
            output_dir.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            raise runtime_error_cls(f"failed to create output directory {output_dir}: {exc}") from exc
        result_path = output_dir / "run_result.json"
        if result_path.exists():
            raise runtime_error_cls(f"explicit output directory already contains {result_path.name}: {output_dir}")
        return output_dir, "explicit"

    primary_output_dir = default_output_dir_fn(run_id)
    try:
        primary_output_dir.mkdir(parents=True, exist_ok=False)
        return primary_output_dir, "default-cache"
    except FileExistsError:
        raise runtime_error_cls(f"default output directory already exists: {primary_output_dir}") from None
    except OSError:
        fallback_dir = fallback_output_dir_fn(run_id)
        try:
            fallback_dir.mkdir(parents=True, exist_ok=False)
        except FileExistsError:
            raise runtime_error_cls(f"fallback output directory already exists: {fallback_dir}") from None
        except OSError as exc:
            raise runtime_error_cls(f"failed to create fallback output directory {fallback_dir}: {exc}") from exc
        return fallback_dir, "fallback-tmp"


def read_input_text(
    args: argparse.Namespace,
    *,
    runtime_error_cls: type[Exception] = RuntimeError,
) -> tuple[str, dict[str, Any]]:
    """Load the primary input text and its source metadata."""
    if args.prompt is not None:
        return args.prompt, {"source": "prompt", "inputFile": None}
    input_path = Path(args.input_file).expanduser()
    try:
        text = input_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise runtime_error_cls(f"failed to read input file {input_path}: {exc}") from exc
    return text, {"source": "input-file", "inputFile": str(input_path)}


def read_inventory(
    path: str | None,
    *,
    runtime_error_cls: type[Exception] = RuntimeError,
) -> tuple[list[dict[str, Any]], dict[str, Any] | None]:
    """Load optional inventory evidence from JSON or minimal YAML."""
    if not path:
        return [], None
    inventory_path = Path(path).expanduser()
    try:
        raw_text = inventory_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise runtime_error_cls(f"failed to read asset inventory file {inventory_path}: {exc}") from exc

    suffix = inventory_path.suffix.lower()
    try:
        if suffix == ".json":
            payload = json.loads(raw_text)
        else:
            payload = parse_minimal_yaml(raw_text)
    except (json.JSONDecodeError, ValueError) as exc:
        raise runtime_error_cls(f"failed to parse asset inventory file {inventory_path}: {exc}") from exc

    assets = normalize_assets(payload)
    metadata = {"path": str(inventory_path), "assetCount": len(assets)}
    return assets, metadata


def persist_result(output_dir: Path, result: dict[str, Any]) -> dict[str, Any]:
    """Persist run-scoped semirun artifacts for the current shadow execution."""
    output_dir.mkdir(parents=True, exist_ok=True)
    result_path = output_dir / "run_result.json"
    governance_path: Path | None = None
    artifact_payload = governance_artifact_payload(result)
    if artifact_payload is not None:
        asset_id = artifact_payload["governance_review"]["asset_id"]
        governance_path = output_dir / f"governance-review-{safe_slug(asset_id)}-{safe_slug(result['runId'])}.yaml"
        governance_path.write_text(dump_governance_yaml(artifact_payload), encoding="utf-8")
    result["artifacts"]["runResultJson"] = str(result_path)
    result["artifacts"]["governanceReviewYaml"] = str(governance_path) if governance_path else None
    result_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    return result
