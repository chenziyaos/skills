from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).with_name("preflight.sh")


class PreflightScriptTest(unittest.TestCase):
    def test_skips_publish_config_when_scope_missing(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            changeset_dir = repo / ".changeset"
            changeset_dir.mkdir(parents=True)
            (changeset_dir / "config.json").write_text("{}\n", encoding="utf-8")

            bnpm = repo / "bnpm"
            bnpm.write_text("#!/usr/bin/env bash\nexit 0\n", encoding="utf-8")
            bnpm.chmod(0o755)

            npm = repo / "npm"
            npm.write_text("#!/usr/bin/env bash\nif [ \"$1\" = \"whoami\" ]; then exit 0; fi\nexit 0\n", encoding="utf-8")
            npm.chmod(0o755)

            completed = subprocess.run(
                ["bash", str(SCRIPT)],
                cwd=repo,
                env={"PATH": f"{repo}:{Path('/usr/bin')}:{Path('/bin')}"},
                capture_output=True,
                text=True,
                check=False,
            )

        self.assertEqual(completed.returncode, 0)
        self.assertIn("未指定 scope，跳过 publishConfig 检查", completed.stdout)
        self.assertIn("All preflight checks passed", completed.stdout)


if __name__ == "__main__":
    unittest.main()
