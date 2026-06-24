from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from clean import Report, scan_audit_snapshots


class CleanSnapshotsTest(unittest.TestCase):
    def test_scan_audit_snapshots_prefers_snapshots_directory(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            state_dir = Path(temp_dir) / ".skill-refiner"
            snapshots_dir = state_dir / "snapshots"
            snapshots_dir.mkdir(parents=True)
            for name in ("2026-06-01.json", "2026-06-08.json", "2026-06-15.json"):
                (snapshots_dir / name).write_text("{}\n", encoding="utf-8")

            report = Report()
            scan_audit_snapshots("skill-refiner", state_dir, keep=2, report=report)

        self.assertEqual(len(report.actions), 1)
        self.assertEqual(report.actions[0].path.name, "2026-06-01.json")
        self.assertIn("audit snapshots", report.actions[0].reason)


if __name__ == "__main__":
    unittest.main()
