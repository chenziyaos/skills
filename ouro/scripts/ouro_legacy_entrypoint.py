#!/usr/bin/env python3
"""Compatibility entrypoint for the Ouro shadow runtime."""
from __future__ import annotations

import warnings

from run_ouro import main


if __name__ == "__main__":
    warnings.warn(
        "scripts/ouro_legacy_entrypoint.py is compatibility-only; use scripts/run_ouro.py or python3 -m ouro instead.",
        DeprecationWarning,
        stacklevel=1,
    )
    raise SystemExit(main())
