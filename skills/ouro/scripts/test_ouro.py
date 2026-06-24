from __future__ import annotations

import importlib
import unittest

TEST_MODULES = (
    "tests.test_analysis",
    "tests.test_cli_runtime",
    "tests.test_control_plane",
    "tests.test_governance",
    "tests.test_host_bridge",
    "tests.test_runtime_io",
    "tests.test_text_utils",
)


def load_tests(loader: unittest.TestLoader, _: unittest.TestSuite, __: str | None) -> unittest.TestSuite:
    suite = unittest.TestSuite()
    for module_name in TEST_MODULES:
        suite.addTests(loader.loadTestsFromModule(importlib.import_module(module_name)))
    return suite


if __name__ == "__main__":
    unittest.main()
