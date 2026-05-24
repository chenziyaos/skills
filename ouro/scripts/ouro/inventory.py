"""Inventory parsing helpers for the Ouro shadow runtime."""
from __future__ import annotations

from typing import Any


def parse_minimal_yaml(raw_text: str) -> Any:
    """Parse the small YAML subset used by Ouro reference artifacts."""
    lines = [line.rstrip() for line in raw_text.splitlines() if line.strip() and not line.lstrip().startswith("#")]
    if not lines:
        return {}
    if lines[0].startswith("governance_review:"):
        return {"governance_review": parse_key_value_block(lines[1:])}
    if lines[0].startswith("assets:"):
        assets: list[dict[str, Any]] = []
        current: dict[str, Any] | None = None
        for line in lines[1:]:
            stripped = line.strip()
            if stripped.startswith("- "):
                current = {}
                assets.append(current)
                stripped = stripped[2:]
                if stripped:
                    key, value = split_key_value(stripped)
                    current[key] = parse_scalar(value)
                continue
            if current is None:
                raise ValueError(f"unsupported YAML line: {stripped}")
            key, value = split_key_value(stripped)
            current[key] = parse_scalar(value)
        return {"assets": assets}
    return parse_key_value_block(lines)


def parse_key_value_block(lines: list[str]) -> dict[str, Any]:
    """Parse a flat YAML-like key-value block."""
    result: dict[str, Any] = {}
    current_list_key: str | None = None
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("- ") and current_list_key is not None:
            result.setdefault(current_list_key, []).append(parse_scalar(stripped[2:]))
            continue
        key, value = split_key_value(stripped)
        if value == "":
            result[key] = []
            current_list_key = key
            continue
        result[key] = parse_scalar(value)
        current_list_key = None
    return result


def split_key_value(text: str) -> tuple[str, str]:
    """Split a YAML-style key-value line."""
    if ":" not in text:
        raise ValueError(f"unsupported YAML line: {text}")
    key, value = text.split(":", 1)
    return key.strip(), value.strip()


def parse_scalar(value: str) -> Any:
    """Parse a simple scalar or inline list value."""
    if value in {"null", "None"}:
        return None
    if value == "true":
        return True
    if value == "false":
        return False
    if value.startswith("[") and value.endswith("]"):
        inner = value[1:-1].strip()
        if not inner:
            return []
        return [item.strip().strip('"\'') for item in inner.split(",") if item.strip()]
    if value.startswith('"') and value.endswith('"'):
        return value[1:-1]
    if value.startswith("'") and value.endswith("'"):
        return value[1:-1]
    return value


def normalize_assets(payload: Any) -> list[dict[str, Any]]:
    """Normalize a parsed inventory payload into an asset list."""
    if isinstance(payload, list):
        raw_assets = payload
    elif isinstance(payload, dict):
        raw_assets = payload.get("assets") or []
    else:
        raw_assets = []
    assets: list[dict[str, Any]] = []
    for item in raw_assets:
        if not isinstance(item, dict):
            continue
        asset = {
            "asset_id": item.get("asset_id") or item.get("assetId"),
            "asset_type": item.get("asset_type") or item.get("assetType"),
            "scope": item.get("scope"),
            "successor_of": item.get("successor_of") or item.get("successorOf"),
            "merged_into": item.get("merged_into") or item.get("mergedInto"),
            "depends_on": normalize_list(item.get("depends_on") or item.get("dependsOn") or []),
        }
        if asset["asset_id"]:
            assets.append(asset)
    return assets


def normalize_list(value: Any) -> list[str]:
    """Normalize a list-like field to a list of strings."""
    if isinstance(value, list):
        return [str(item) for item in value if item is not None]
    if value in (None, ""):
        return []
    return [str(value)]
