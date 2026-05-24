"""Shadow-only control-plane advisory helpers for the Ouro runtime."""
from __future__ import annotations

import re
from typing import Any

from .host_bridge import HostBridgeSnapshot
from .models import PriorEvidenceSummary
from .text_utils import split_direct_and_protected_text

CONTROL_COMMAND_PATTERNS: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"\bouro:\s*self-digest\b", re.IGNORECASE), "self-digest"),
    (re.compile(r"\bouro:\s*export-ledger\b", re.IGNORECASE), "export-ledger"),
    (re.compile(r"\bouro:\s*import-ledger\b", re.IGNORECASE), "import-ledger"),
    (re.compile(r"\bouro:\s*status\b", re.IGNORECASE), "status"),
)
PREVIEW_MUTATION_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"preview-first", re.IGNORECASE),
    re.compile(r"preview first", re.IGNORECASE),
    re.compile(r"diff/patch/plan", re.IGNORECASE),
    re.compile(r"只允许\s*diff/patch/plan", re.IGNORECASE),
)
CONTROL_NOTES = {
    "self-digest": "Shadow runtime can emit a self-digest advisory only; it does not rewrite durable skill, rule, config, or ledger state.",
    "export-ledger": "Shadow runtime can describe an export plan only; it does not emit durable ledger JSON from host memory.",
    "import-ledger": "Shadow runtime can describe an import plan only; it does not append ledger records or mutate host memory.",
    "status": "Shadow runtime can emit a run-scoped Health Pulse preview only; it does not scan or mutate durable ledger state.",
    "preview-mutation": "Shadow runtime can emit a preview-first mutation advisory only; it does not mutate skill, rule, agent config, or ledger state.",
}
CONTROL_NEXT_ACTIONS = {
    "self-digest": "Preview the allowed self-digest diff before any real host-backed rewrite path is considered.",
    "export-ledger": "Preview the export source and require host.memory.read before any real ledger export is attempted.",
    "import-ledger": "Preview deduplication and validation steps before any real ledger import path is allowed.",
    "status": "Review the run-scoped Health Pulse preview before using any real host status command.",
    "preview-mutation": "Keep the outcome at diff/patch/plan preview only until an explicit confirmation and real mutation gateway exist.",
}
CONTROL_REQUIRED_CAPABILITIES = {
    "self-digest": ("host.memory.read", "host.memory.append", "host.config-manager.apply"),
    "export-ledger": ("host.memory.read",),
    "import-ledger": ("host.memory.append",),
    "status": (),
    "preview-mutation": (),
}


def detect_control_command(text: str) -> str | None:
    """Detect a shadow control-plane directive from direct user text only."""
    direct_text, _ = split_direct_and_protected_text(text)
    for pattern, command in CONTROL_COMMAND_PATTERNS:
        if pattern.search(direct_text):
            return command
    if any(pattern.search(direct_text) for pattern in PREVIEW_MUTATION_PATTERNS):
        return "preview-mutation"
    return None



def build_control_plane_advisory(
    text: str,
    host_bridge: HostBridgeSnapshot,
    retrieval_mode: str,
    prior_summary: PriorEvidenceSummary,
) -> dict[str, Any]:
    """Build a run-scoped advisory control-plane surface without executing commands."""
    command = detect_control_command(text)
    if command is None:
        return {
            "requested": False,
            "command": None,
            "mode": "shadow-advisory",
            "previewRequired": False,
            "executionState": "not-requested",
            "mutationAllowed": False,
            "ledgerWriteAllowed": False,
            "selfDigestAllowed": False,
            "requiredCapabilities": [],
            "availableCapabilities": [],
            "missingCapabilities": [],
            "healthPulsePreview": None,
            "notes": "No control-plane directive was detected in this run.",
            "nextAction": None,
        }

    required_capabilities = list(CONTROL_REQUIRED_CAPABILITIES[command])
    available_capabilities = [
        capability
        for capability in required_capabilities
        if host_bridge.capability_available(capability)
    ]
    missing_capabilities = [
        capability
        for capability in required_capabilities
        if not host_bridge.capability_available(capability)
    ]
    health_pulse_preview = None
    if command == "status":
        health_pulse_preview = {
            "retrievalMode": retrieval_mode,
            "ledgerSizeBucket": host_bridge.ledger_size_bucket,
            "ledgerPriorCount": prior_summary.count,
            "pendingOutcomeCount": prior_summary.unresolved_count,
            "readOnly": True,
        }

    return {
        "requested": True,
        "command": command,
        "mode": "shadow-advisory",
        "previewRequired": command != "status",
        "executionState": "preview-only",
        "mutationAllowed": False,
        "ledgerWriteAllowed": False,
        "selfDigestAllowed": False,
        "requiredCapabilities": required_capabilities,
        "availableCapabilities": available_capabilities,
        "missingCapabilities": missing_capabilities,
        "healthPulsePreview": health_pulse_preview,
        "notes": CONTROL_NOTES[command],
        "nextAction": CONTROL_NEXT_ACTIONS[command],
    }
