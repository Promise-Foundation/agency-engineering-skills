#!/usr/bin/env python3
"""Publish Promisify's shared domain context without deriving host skill models.

LTP and Hypothesize own and publish their own domain-addressed artifacts. This
builder deliberately does not convert promises into LTP necessary conditions or
hypotheses. Future exporters may persist plugin `promiseTypes` contributions as
Promisify subdomains while preserving the host object's identity and meaning.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
UI_ROOT = REPOSITORY_ROOT / "agency-ui"
EXPLORER_PATH = UI_ROOT / "apps/web/public/api/promisify/explorer.json"
PROMISIFY_CLI = REPOSITORY_ROOT / "promisify/scripts/norms.py"


def main() -> int:
    subprocess.run(
        [sys.executable, str(PROMISIFY_CLI), "validate", str(REPOSITORY_ROOT)],
        check=True,
    )
    subprocess.run(
        [
            sys.executable,
            str(PROMISIFY_CLI),
            "explorer",
            str(REPOSITORY_ROOT),
            "--output",
            str(EXPLORER_PATH),
        ],
        check=True,
    )
    print(f"wrote {EXPLORER_PATH.relative_to(REPOSITORY_ROOT)}")
    print("LTP and Hypothesize artifacts remain owned by their generators")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
