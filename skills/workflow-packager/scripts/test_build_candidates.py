from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from build_candidates import has_secret, is_one_off, is_ouro_candidate, redact


class BuildCandidatesHelpersTest(unittest.TestCase):
    def test_has_secret_detects_keywords(self) -> None:
        self.assertTrue(has_secret("please use this api_key for the workflow"))

    def test_has_secret_detects_email(self) -> None:
        self.assertTrue(has_secret("contact alice@example.com before publishing"))

    def test_redact_masks_detected_patterns(self) -> None:
        self.assertEqual(redact("email alice@example.com"), "email [REDACTED]")

    def test_is_one_off_recognizes_ad_hoc_language(self) -> None:
        self.assertTrue(is_one_off("just this once, do a temporary release workaround"))
        self.assertFalse(is_one_off("weekly release checklist"))

    def test_is_ouro_candidate_detects_external_material(self) -> None:
        self.assertEqual(is_ouro_candidate("absorb https://example.com/spec into a skill"), "samples contain URL(s)")
        self.assertIn("external git repo", is_ouro_candidate("digest github.com/example/repo into a reusable capability"))


if __name__ == "__main__":
    unittest.main()
