"""Modular test suite for the Ouro shadow runtime."""
from __future__ import annotations

import importlib
import sys

sys.modules.setdefault("support", importlib.import_module("tests.support"))
