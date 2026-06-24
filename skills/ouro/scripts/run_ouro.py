#!/usr/bin/env python3
"""Stable entrypoint for the Ouro shadow runtime."""
from __future__ import annotations

import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from ouro.cli import main


if __name__ == "__main__":
    raise SystemExit(main())
