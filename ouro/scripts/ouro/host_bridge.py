"""Host bridge snapshot for the Ouro shadow runtime."""
from __future__ import annotations

import argparse
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any


class HostBridgeError(RuntimeError):
    """Raised when the shadow host bridge payload is invalid or unreadable."""


CAPABILITY_DEFAULTS = {
    "host.fetch.url": False,
    "host.fetch.repo": False,
    "host.fs": False,
    "host.skill.list": False,
    "host.skill.create": False,
    "host.skill.update": False,
    "host.search": False,
    "host.embed": False,
    "host.exec": False,
    "host.transcribe": False,
    "host.memory.append": False,
    "host.memory.read": False,
    "host.memory.search": False,
    "host.time.now": True,
    "host.list_capabilities": False,
    "host.mode": True,
    "host.tenant_id": True,
    "host.config-manager.apply": False,
}

CONCEPTUAL_CAPABILITY_GROUPS = {
    "host.fetch": ("host.fetch.url", "host.fetch.repo"),
    "host.fs": ("host.fs",),
    "host.skill": ("host.skill.list", "host.skill.create", "host.skill.update"),
    "host.search": ("host.search",),
    "host.embed": ("host.embed",),
    "host.exec": ("host.exec",),
    "host.transcribe": ("host.transcribe",),
    "host.memory": ("host.memory.append", "host.memory.read", "host.memory.search"),
    "host.time.now": ("host.time.now",),
    "host.list_capabilities": ("host.list_capabilities",),
    "host.mode": ("host.mode",),
    "host.tenant_id": ("host.tenant_id",),
    "host.config-manager.apply": ("host.config-manager.apply",),
}

CAPABILITY_ALIASES = {
    "fetch.url": "host.fetch.url",
    "fetch.repo": "host.fetch.repo",
    "fs": "host.fs",
    "skill.list": "host.skill.list",
    "skill.create": "host.skill.create",
    "skill.update": "host.skill.update",
    "search": "host.search",
    "embed": "host.embed",
    "exec": "host.exec",
    "transcribe": "host.transcribe",
    "memory.append": "host.memory.append",
    "memory.read": "host.memory.read",
    "memory.search": "host.memory.search",
    "time.now": "host.time.now",
    "list_capabilities": "host.list_capabilities",
    "mode": "host.mode",
    "tenant_id": "host.tenant_id",
    "config-manager.apply": "host.config-manager.apply",
}


@dataclass(frozen=True)
class HostBridgeSnapshot:
    """Normalized host capability view consumed by the shadow runtime."""

    capabilities: dict[str, bool]
    mode: str
    tenant_id: str
    source: str
    read_only: bool
    ledger_size_bucket: str
    skill_registry: tuple[dict[str, Any], ...] = ()
    memory_hits: tuple[dict[str, Any], ...] = ()
    ledger_records: tuple[dict[str, Any], ...] = ()
    time_now: str | None = None

    @property
    def retrieval_mode(self) -> str:
        if self.capabilities.get("host.memory.search", False):
            return "memory-search"
        if self.capabilities.get("host.memory.read", False):
            return "memory-read-bm25"
        return "context-only"

    @property
    def discovery_mode(self) -> str:
        return "active" if self.capabilities.get("host.list_capabilities", False) else "passive"

    @property
    def observed_assets(self) -> list[dict[str, Any]]:
        return [*self.skill_registry, *self.memory_hits]

    def capability_available(self, capability_id: str) -> bool:
        return self.capabilities.get(capability_id, False)

    def to_result_dict(self) -> dict[str, Any]:
        conceptual_capabilities = {
            name: any(self.capabilities.get(capability, False) for capability in members)
            for name, members in CONCEPTUAL_CAPABILITY_GROUPS.items()
        }
        return {
            "memorySearch": self.capability_available("host.memory.search"),
            "memoryRead": self.capability_available("host.memory.read"),
            "listCapabilities": self.capability_available("host.list_capabilities"),
            "exec": self.capability_available("host.exec"),
            "ledgerSizeBucket": self.ledger_size_bucket,
            "mode": self.mode,
            "tenantId": self.tenant_id,
            "discoveryMode": self.discovery_mode,
            "retrievalMode": self.retrieval_mode,
            "readOnly": self.read_only,
            "bridgeSource": self.source,
            "skillRegistryCount": len(self.skill_registry),
            "memoryHitCount": len(self.memory_hits),
            "ledgerRecordCount": len(self.ledger_records),
            "observedAssetCount": len(self.observed_assets),
            "timeNow": self.time_now,
            "capabilities": self.capabilities,
            "conceptualCapabilities": conceptual_capabilities,
        }


@dataclass(frozen=True)
class HostBridgeProviderData:
    """Resolved read-only provider inputs before snapshot normalization."""

    capabilities: dict[str, bool]
    mode: str
    tenant_id: str
    ledger_size_bucket: str
    skill_registry: tuple[dict[str, Any], ...] = ()
    memory_hits: tuple[dict[str, Any], ...] = ()
    ledger_records: tuple[dict[str, Any], ...] = ()
    time_now: str | None = None


def canonical_capability_id(name: str) -> str | None:
    """Normalize a capability id or host-side alias to the canonical contract key."""
    lowered = name.strip().lower()
    if not lowered:
        return None
    if lowered in CAPABILITY_DEFAULTS:
        return lowered
    return CAPABILITY_ALIASES.get(lowered)


def normalize_asset_records(raw_assets: Any, source: str) -> tuple[dict[str, Any], ...]:
    """Normalize host bridge asset records to the runtime asset schema."""
    if not isinstance(raw_assets, list):
        return ()
    assets: list[dict[str, Any]] = []
    for item in raw_assets:
        if not isinstance(item, dict):
            continue
        asset_id = item.get("asset_id") or item.get("assetId")
        if not asset_id:
            continue
        depends_on = item.get("depends_on") or item.get("dependsOn") or []
        if isinstance(depends_on, list):
            normalized_dependencies = [str(value) for value in depends_on if value is not None]
        elif depends_on in (None, ""):
            normalized_dependencies = []
        else:
            normalized_dependencies = [str(depends_on)]
        assets.append(
            {
                "asset_id": str(asset_id),
                "asset_type": item.get("asset_type") or item.get("assetType"),
                "scope": item.get("scope"),
                "successor_of": item.get("successor_of") or item.get("successorOf"),
                "merged_into": item.get("merged_into") or item.get("mergedInto"),
                "depends_on": normalized_dependencies,
                "evidence_sources": [source],
            }
        )
    return tuple(assets)


def normalize_ledger_records(raw_records: Any, source: str) -> tuple[dict[str, Any], ...]:
    """Normalize read-only ledger records into a compact runtime-facing shape."""
    if not isinstance(raw_records, list):
        return ()
    records: list[dict[str, Any]] = []
    for item in raw_records:
        if not isinstance(item, dict):
            continue
        input_payload = item.get("input") if isinstance(item.get("input"), dict) else {}
        records.append(
            {
                "id": item.get("id"),
                "decision": item.get("decision"),
                "target": item.get("target"),
                "outcome": item.get("outcome"),
                "input": {
                    "sha256_12": input_payload.get("sha256_12"),
                    "summary": input_payload.get("summary"),
                    "uri": input_payload.get("uri"),
                },
                "evidence_sources": [source],
            }
        )
    return tuple(records)


def normalize_capabilities(raw_capabilities: Any) -> dict[str, bool]:
    """Normalize capability ids from a host bridge payload."""
    capabilities = dict(CAPABILITY_DEFAULTS)
    if not isinstance(raw_capabilities, dict):
        return capabilities
    for key, value in raw_capabilities.items():
        canonical = canonical_capability_id(str(key))
        if canonical is None:
            continue
        capabilities[canonical] = bool(value)
    return capabilities


def read_host_bridge_payload(path: str) -> dict[str, Any]:
    """Read a structured host bridge snapshot from disk."""
    bridge_path = Path(path).expanduser()
    try:
        raw_text = bridge_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise HostBridgeError(f"failed to read host bridge file {bridge_path}: {exc}") from exc
    try:
        payload = json.loads(raw_text)
    except json.JSONDecodeError as exc:
        raise HostBridgeError(f"failed to parse host bridge file {bridge_path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise HostBridgeError(f"host bridge file {bridge_path} must contain a JSON object")
    return payload


def build_host_bridge_snapshot(
    *,
    capabilities: dict[str, bool],
    mode: str,
    tenant_id: str,
    source: str,
    ledger_size_bucket: str,
    skill_registry: tuple[dict[str, Any], ...] = (),
    memory_hits: tuple[dict[str, Any], ...] = (),
    ledger_records: tuple[dict[str, Any], ...] = (),
    time_now: str | None = None,
) -> HostBridgeSnapshot:
    """Build a normalized read-only snapshot from already-resolved provider data."""
    normalized_mode = mode if mode in {"interactive", "unattended"} else "interactive"
    normalized_bucket = ledger_size_bucket if ledger_size_bucket in {"0", "1-20", "21+"} else "0"
    return HostBridgeSnapshot(
        capabilities=capabilities,
        mode=normalized_mode,
        tenant_id=tenant_id or "default",
        source=source,
        read_only=True,
        ledger_size_bucket=normalized_bucket,
        skill_registry=skill_registry,
        memory_hits=memory_hits,
        ledger_records=ledger_records,
        time_now=time_now,
    )


def provider_data_from_payload(payload: dict[str, Any], *, fallback_ledger_size_bucket: str) -> HostBridgeProviderData:
    """Resolve normalized provider data from a structured host bridge payload."""
    capabilities = normalize_capabilities(payload.get("capabilities") or payload.get("hostCapabilities") or {})
    mode = str(payload.get("mode") or "interactive")
    tenant_id = str(payload.get("tenant_id") or payload.get("tenantId") or "default")
    ledger_size_bucket = str(payload.get("ledger_size_bucket") or payload.get("ledgerSizeBucket") or fallback_ledger_size_bucket)
    if ledger_size_bucket not in {"0", "1-20", "21+"}:
        ledger_size_bucket = fallback_ledger_size_bucket
    skill_registry = normalize_asset_records(payload.get("skills") or payload.get("skillRegistry") or [], "host-skill-registry")
    memory_hits = normalize_asset_records(payload.get("memory_hits") or payload.get("memoryHits") or [], "host-memory-search")
    ledger_records = normalize_ledger_records(payload.get("ledger_records") or payload.get("ledgerRecords") or [], "host-memory-read")
    time_now = payload.get("time_now") or payload.get("timeNow")
    return HostBridgeProviderData(
        capabilities=capabilities,
        mode=mode,
        tenant_id=tenant_id,
        ledger_size_bucket=ledger_size_bucket,
        skill_registry=skill_registry,
        memory_hits=memory_hits,
        ledger_records=ledger_records,
        time_now=str(time_now) if time_now is not None else None,
    )


def provider_data_from_cli_args(args: argparse.Namespace) -> HostBridgeProviderData:
    """Resolve normalized provider data from CLI flags or environment-backed read-only inputs."""
    capabilities = dict(CAPABILITY_DEFAULTS)
    capabilities["host.memory.search"] = args.host_memory_search == "yes"
    capabilities["host.list_capabilities"] = args.host_list_capabilities == "yes"
    capabilities["host.exec"] = args.host_exec == "yes"

    provider_payload_path = os.environ.get("OURO_HOST_PROVIDER_FILE")
    if provider_payload_path:
        payload = read_host_bridge_payload(provider_payload_path)
        provider_data = provider_data_from_payload(payload, fallback_ledger_size_bucket=args.ledger_size_bucket)
        merged_capabilities = dict(capabilities)
        merged_capabilities.update(provider_data.capabilities)
        return HostBridgeProviderData(
            capabilities=merged_capabilities,
            mode=provider_data.mode,
            tenant_id=provider_data.tenant_id,
            ledger_size_bucket=provider_data.ledger_size_bucket,
            skill_registry=provider_data.skill_registry,
            memory_hits=provider_data.memory_hits,
            ledger_records=provider_data.ledger_records,
            time_now=provider_data.time_now,
        )

    time_now = os.environ.get("OURO_HOST_TIME_NOW")
    tenant_id = os.environ.get("OURO_HOST_TENANT_ID", "default")
    mode = os.environ.get("OURO_HOST_MODE", "interactive")
    ledger_records = normalize_ledger_records(
        json.loads(os.environ["OURO_HOST_LEDGER_RECORDS"])
        if os.environ.get("OURO_HOST_LEDGER_RECORDS")
        else [],
        "host-memory-read",
    )
    if ledger_records:
        capabilities["host.memory.read"] = True
    return HostBridgeProviderData(
        capabilities=capabilities,
        mode=mode,
        tenant_id=tenant_id,
        ledger_size_bucket=args.ledger_size_bucket,
        ledger_records=ledger_records,
        time_now=time_now,
    )


def build_host_bridge_from_payload(
    payload: dict[str, Any],
    *,
    source: str,
    fallback_ledger_size_bucket: str,
) -> HostBridgeSnapshot:
    """Build a normalized host bridge snapshot from structured payload data."""
    provider_data = provider_data_from_payload(payload, fallback_ledger_size_bucket=fallback_ledger_size_bucket)
    return build_host_bridge_snapshot(
        capabilities=provider_data.capabilities,
        mode=provider_data.mode,
        tenant_id=provider_data.tenant_id,
        source=source,
        ledger_size_bucket=provider_data.ledger_size_bucket,
        skill_registry=provider_data.skill_registry,
        memory_hits=provider_data.memory_hits,
        ledger_records=provider_data.ledger_records,
        time_now=provider_data.time_now,
    )


def build_host_bridge(args: argparse.Namespace) -> HostBridgeSnapshot:
    """Build the read-only capability snapshot used by the shadow runtime."""
    host_bridge_file = getattr(args, "host_bridge_file", None)
    if host_bridge_file:
        payload = read_host_bridge_payload(host_bridge_file)
        return build_host_bridge_from_payload(
            payload,
            source="host-bridge-file",
            fallback_ledger_size_bucket=args.ledger_size_bucket,
        )

    provider_data = provider_data_from_cli_args(args)
    source = "host-provider-file" if os.environ.get("OURO_HOST_PROVIDER_FILE") else "cli-flags"
    return build_host_bridge_snapshot(
        capabilities=provider_data.capabilities,
        mode=provider_data.mode,
        tenant_id=provider_data.tenant_id,
        source=source,
        ledger_size_bucket=provider_data.ledger_size_bucket,
        skill_registry=provider_data.skill_registry,
        memory_hits=provider_data.memory_hits,
        ledger_records=provider_data.ledger_records,
        time_now=provider_data.time_now,
    )
