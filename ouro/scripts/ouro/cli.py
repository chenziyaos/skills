"""Shadow runtime for the Ouro skill."""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .analysis import analyze_input, build_evidence_envelope
from .control_plane import build_control_plane_advisory
from .decision import build_decision_explanation, classify_decision
from .governance import build_governance_notes, infer_governance_review
from .host_bridge import HostBridgeError, HostBridgeSnapshot, build_host_bridge
from .models import DecisionResult, EvidenceEnvelope, InputAnalysis
from .observability import build_probe_observability, calibrate_confidence, calibration_messages
from .priors import summarize_ledger_priors
from .reporting import build_result_payload, next_action
from .runtime_io import (
    DEFAULT_CACHE_TTL_HOURS,
    DEFAULT_OUTPUT_ROOT,
    FALLBACK_OUTPUT_ROOT,
    CleanupSummary,
    cleanup_expired_output_dirs,
    default_output_dir,
    ensure_output_dir as runtime_io_ensure_output_dir,
    fallback_output_dir,
    persist_result,
    read_input_text as runtime_io_read_input_text,
    read_inventory as runtime_io_read_inventory,
)
from .text_utils import merge_asset_evidence, redact_sensitive_preview
from .triggering import detect_trigger

class OuroRuntimeError(RuntimeError):
    """Raised when the shadow runtime cannot complete."""


@dataclass(frozen=True)
class RunContext:
    """Stable run-scoped values shared across result building and persistence."""

    run_id: str
    timestamp: str


def current_timestamp() -> datetime:
    """Return the current UTC timestamp."""
    return datetime.now(timezone.utc)


def timestamp_token(now: datetime) -> str:
    """Return a filesystem-safe UTC timestamp token."""
    return now.strftime("%Y%m%dT%H%M%S.%fZ")


def iso_timestamp(now: datetime) -> str:
    """Return an ISO-8601 UTC timestamp with second-level stability."""
    return now.replace(microsecond=0).isoformat()


def build_run_context(text: str, now: datetime | None = None) -> RunContext:
    """Build deterministic run-scoped ids from time plus input hash."""
    observed_now = now or current_timestamp()
    input_hash = short_hash(text)
    token = timestamp_token(observed_now)
    return RunContext(
        run_id=f"run-{token}-{input_hash[:6]}",
        timestamp=iso_timestamp(observed_now),
    )


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse CLI arguments for the Ouro shadow runtime."""
    parser = argparse.ArgumentParser(description="Run the advisory-only Ouro shadow runtime")
    source_group = parser.add_mutually_exclusive_group(required=True)
    source_group.add_argument("--prompt", help="Prompt text to evaluate")
    source_group.add_argument("--input-file", help="Read prompt text from a file")
    parser.add_argument(
        "--asset-inventory-file",
        help="Optional JSON/YAML inventory file used only to strengthen governance evidence",
    )
    parser.add_argument(
        "--output-dir",
        help="Directory for run_result.json and any companion governance artifact",
    )
    parser.add_argument(
        "--host-memory-search",
        choices=("yes", "no"),
        default="no",
        help="Whether the host exposes semantic memory search",
    )
    parser.add_argument(
        "--host-list-capabilities",
        choices=("yes", "no"),
        default="no",
        help="Whether the host can actively enumerate capabilities",
    )
    parser.add_argument(
        "--host-exec",
        choices=("yes", "no"),
        default="no",
        help="Whether the host provides sandboxed execution for dry-runs",
    )
    parser.add_argument(
        "--ledger-size-bucket",
        choices=("0", "1-20", "21+"),
        default="0",
        help="Approximate ledger size used only for confidence calibration",
    )
    parser.add_argument(
        "--host-bridge-file",
        help="Optional JSON host bridge snapshot used to simulate read-only host adapter inputs",
    )
    parser.add_argument(
        "--show-scores",
        action="store_true",
        help="Include routing score breakdown in the JSON result payload",
    )
    parser.add_argument(
        "--explain-decision",
        action="store_true",
        help="Include routing explanation details in the JSON result payload",
    )
    parser.add_argument(
        "--cache-ttl-hours",
        type=int,
        default=DEFAULT_CACHE_TTL_HOURS,
        help="Retention window for auto-managed shadow_run_* directories under the default cache root; use a negative value to disable cleanup",
    )
    return parser.parse_args(argv)


def read_input_text(args: argparse.Namespace) -> tuple[str, dict[str, Any]]:
    """Load the primary input text and its source metadata."""
    return runtime_io_read_input_text(args, runtime_error_cls=OuroRuntimeError)


def read_inventory(path: str | None) -> tuple[list[dict[str, Any]], dict[str, Any] | None]:
    """Load optional inventory evidence from JSON or minimal YAML."""
    return runtime_io_read_inventory(path, runtime_error_cls=OuroRuntimeError)


def ensure_output_dir(path: str | None, run_id: str) -> tuple[Path, str]:
    """Create and return the requested output directory plus output mode."""
    return runtime_io_ensure_output_dir(
        path,
        run_id,
        default_output_dir_fn=lambda value: default_output_dir(value, output_root=Path(DEFAULT_OUTPUT_ROOT)),
        fallback_output_dir_fn=lambda value: fallback_output_dir(value, output_root=Path(FALLBACK_OUTPUT_ROOT)),
        runtime_error_cls=OuroRuntimeError,
    )


def short_hash(text: str) -> str:
    """Return a stable short hash for an input string."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:12]


def retrieval_mode(host_bridge: HostBridgeSnapshot) -> str:
    """Return the retrieval mode label used by the run."""
    return host_bridge.retrieval_mode


def build_run_result(
    args: argparse.Namespace,
    run_context: RunContext | None = None,
    input_payload: tuple[str, dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Build the structured advisory run result for a single Ouro input."""
    text, source_metadata = input_payload or read_input_text(args)
    inventory_assets, inventory_metadata = read_inventory(args.asset_inventory_file)
    host_bridge = build_host_bridge(args)
    assets = merge_asset_evidence(inventory_assets, host_bridge.observed_assets)
    analysis = analyze_input(text, assets)
    evidence = build_evidence_envelope(analysis)
    triggered, trigger_reason, trigger_evidence = detect_trigger(evidence)
    run_context = run_context or build_run_context(text)
    retrieval = retrieval_mode(host_bridge)
    host_snapshot = host_bridge.to_result_dict()
    prior_summary = summarize_ledger_priors(host_bridge.ledger_records)
    control_plane = build_control_plane_advisory(text, host_bridge, retrieval, prior_summary)
    probe = build_probe_observability(host_bridge)

    decision_result: DecisionResult | None = None
    governance_review = {
        "assetId": None,
        "signal": None,
        "evidenceMaturity": None,
        "inventoryEvidencePresent": False,
        "evidenceBasis": [],
        "impactPosture": None,
        "notes": None,
    }
    degradations: list[str] = []
    confidence: str | None = None
    report = {
        "coreValue": "normal summarization or Q&A",
        "reason": "Ouro should only engage when capability-building intent is present.",
        "validationCases": [],
        "rollbackOrContainment": "Route the request to the normal answer path.",
        "nextAction": "Answer the prompt directly instead of creating durable capability artifacts.",
    }

    if triggered:
        decision_result = classify_decision(evidence)
        governance_review = infer_governance_review(evidence, decision_result, assets)
        degradations, confidence_cap = calibration_messages(host_bridge, decision_result, governance_review, prior_summary)
        confidence = calibrate_confidence(decision_result.decision, degradations, confidence_cap)
        report = {
            "coreValue": decision_result.reason,
            "reason": decision_result.reason,
            "validationCases": decision_result.validation_cases,
            "rollbackOrContainment": decision_result.rollback_or_containment,
            "nextAction": next_action(decision_result.decision, governance_review),
        }

    observability = None
    if args.show_scores or args.explain_decision:
        observability = {
            "showScores": args.show_scores,
            "explainDecision": args.explain_decision,
        }
        if args.show_scores:
            observability["scoreBreakdown"] = decision_result.scores if decision_result is not None else None
        if args.explain_decision:
            observability["decisionExplanation"] = build_decision_explanation(
                evidence,
                decision_result,
                triggered,
                trigger_reason,
                trigger_evidence,
            )

    return build_result_payload(
        text=text,
        source_metadata=source_metadata,
        inventory_metadata=inventory_metadata,
        retrieval=retrieval,
        run_id=run_context.run_id,
        timestamp=run_context.timestamp,
        input_hash=short_hash(text),
        host_snapshot=host_snapshot,
        triggered=triggered,
        trigger_reason=trigger_reason,
        trigger_evidence=trigger_evidence,
        evidence=evidence,
        probe=probe,
        decision=decision_result.decision if decision_result is not None else None,
        confidence=confidence,
        degradations=degradations,
        report=report,
        governance_review=governance_review,
        prior_summary=prior_summary,
        control_plane=control_plane,
        observability=observability,
        output_policy=None,
    )


def print_result(result: dict[str, Any]) -> None:
    """Print the structured run result to stdout."""
    print(json.dumps(result, ensure_ascii=False, indent=2))


def main(argv: list[str] | None = None) -> int:
    """Execute the Ouro shadow runtime."""
    try:
        args = parse_args(argv)
        input_payload = read_input_text(args)
        input_text, _ = input_payload
        observed_now = current_timestamp()
        run_context = build_run_context(input_text, observed_now)
        output_dir, output_mode = runtime_io_ensure_output_dir(
            args.output_dir,
            run_context.run_id,
            default_output_dir_fn=lambda value: default_output_dir(value, output_root=Path(DEFAULT_OUTPUT_ROOT)),
            fallback_output_dir_fn=lambda value: fallback_output_dir(value, output_root=Path(FALLBACK_OUTPUT_ROOT)),
            runtime_error_cls=OuroRuntimeError,
        )
        cleanup_summary = CleanupSummary(removed_count=0, removed_sample=())
        managed_root: Path | None = None
        if output_mode == "default-cache":
            managed_root = DEFAULT_OUTPUT_ROOT
            cleanup_summary = cleanup_expired_output_dirs(
                managed_root,
                observed_now,
                args.cache_ttl_hours,
                {output_dir.name},
            )
        elif output_mode == "fallback-tmp":
            managed_root = FALLBACK_OUTPUT_ROOT
            cleanup_summary = cleanup_expired_output_dirs(
                managed_root,
                observed_now,
                args.cache_ttl_hours,
                {output_dir.name},
            )
        result = build_run_result(args, run_context, input_payload=input_payload)
        result["outputPolicy"] = {
            "outputMode": output_mode,
            "cacheTtlHours": args.cache_ttl_hours,
            "managedRoot": str(managed_root) if managed_root else None,
            "expiredRunDirsRemovedCount": cleanup_summary.removed_count,
            "expiredRunDirsSample": list(cleanup_summary.removed_sample),
            "cleanupWarnings": list(cleanup_summary.warnings),
        }
        persisted = persist_result(output_dir, result)
        print_result(persisted)
        return 0
    except (OuroRuntimeError, HostBridgeError, ValueError, OSError, PermissionError) as exc:
        print(
            json.dumps(
                {
                    "mode": "error",
                    "error": str(exc),
                    "actionableHints": [
                        "Check the input file path and encoding.",
                        "If you pass an asset inventory file, keep it in JSON or the minimal YAML subset.",
                        "If you pass a host bridge file, keep it as a JSON object with normalized capability fields.",
                        "If the default output path is unavailable, rerun with --output-dir pointing to a writable directory.",
                    ],
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
