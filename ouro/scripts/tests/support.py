from __future__ import annotations

import importlib
import json
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

SKILL_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_DIR = SKILL_ROOT / "scripts"
WRAPPER = SCRIPTS_DIR / "run_ouro.py"
if str(SCRIPTS_DIR) in sys.path:
    sys.path.remove(str(SCRIPTS_DIR))
sys.path.insert(0, str(SCRIPTS_DIR))
sys.modules.pop("ouro", None)
sys.modules.pop("ouro.cli", None)

runtime = importlib.import_module("ouro.cli")
host_bridge = importlib.import_module("ouro.host_bridge")
text_utils = importlib.import_module("ouro.text_utils")


def make_analysis(**overrides: object) -> runtime.InputAnalysis:
    defaults = {
        "explicit_trigger": False,
        "protected_source_present": False,
        "protected_trigger_names": (),
        "protected_injection_tokens": (),
        "behavior_trigger_tokens": (),
        "capability_context_tokens": (),
        "raw_url_present": False,
        "raw_url_only": False,
        "semantic_false_positive": False,
        "workflow_tokens": (),
        "structured_workflow_tokens": (),
        "validation_tokens": (),
        "rollback_signal": False,
        "overlap_tokens": (),
        "global_behavior_tokens": (),
        "rule_tokens": (),
        "policy_tokens": (),
        "agent_md_tokens": (),
        "one_off_knowledge": False,
        "vague_intent": False,
        "injection_pressure": False,
        "retirement_pressure": False,
        "retirement_risk": False,
        "stale_signal": False,
        "successor_signal": False,
        "merge_signal": False,
        "asset_ids": (),
        "inventory_evidence_present": False,
        "bullet_count": 0,
    }
    defaults.update(overrides)
    return runtime.InputAnalysis(**defaults)


class OuroShadowRuntimeTestCase(unittest.TestCase):
    def run_prompt(self, prompt: str, *extra_args: str) -> dict:
        args = runtime.parse_args(["--prompt", prompt, *extra_args])
        return runtime.build_run_result(args)

    def run_file_input(self, path: Path, *extra_args: str) -> dict:
        args = runtime.parse_args(["--input-file", str(path), *extra_args])
        return runtime.build_run_result(args)
