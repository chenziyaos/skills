from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from build_report import format_findings, format_suggested_edits, format_transcript


class BuildReportFormattingTest(unittest.TestCase):
    def test_format_findings_renders_badges_and_hints(self) -> None:
        output = format_findings([
            {
                "rule": "missing-version",
                "severity": "warn",
                "message": "frontmatter has no `version` field",
                "hint": "Add `version: v0.1.0` to track changes",
            }
        ])
        self.assertIn("[warn] **missing-version**", output)
        self.assertIn("Add `version: v0.1.0`", output)

    def test_format_suggested_edits_uses_priority_order(self) -> None:
        output = format_suggested_edits(
            {
                "findings": [
                    {"rule": "size-hard", "message": "too long"},
                    {"rule": "missing-allowed-tools", "message": "missing"},
                ]
            }
        )
        self.assertLess(output.index("Add `allowed-tools:`"), output.index("REQUIRED: move long sections"))

    def test_format_transcript_groups_signals_by_tier(self) -> None:
        output = format_transcript(
            {
                "scanned_files": 1,
                "summary": {"hits_total": 2, "tier1_total": 1, "tier2_total": 1},
                "hits": [
                    {
                        "file": "/tmp/session.jsonl",
                        "signals": [
                            {"turn_idx": 3, "kind": "retry", "snippet": "did not trigger", "tier": 1},
                            {"turn_idx": 4, "kind": "mention", "snippet": "check this later", "tier": 2},
                        ],
                    }
                ],
            }
        )
        self.assertIn("Tier 1 — High-confidence friction", output)
        self.assertIn("Tier 2 — Worth review", output)
        self.assertIn("did not trigger", output)
        self.assertIn("check this later", output)


if __name__ == "__main__":
    unittest.main()
