#!/usr/bin/env python3
"""Regenerate the committed render golden under ``tests/golden/``.

Run after an intentional renderer change:

    python tests/regen_golden.py
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ltp.renderers import render_all  # noqa: E402
from ltp.store import load_model  # noqa: E402

GOLDEN = ROOT / "tests" / "golden"
CASES = {"compound-cause": ROOT / "evals" / "fixtures" / "valid" / "compound-cause" / "ltp-model.yaml"}


def main() -> int:
    for name, model_path in CASES.items():
        target = GOLDEN / name
        if target.exists():
            shutil.rmtree(target)
        files = render_all(load_model(model_path))
        for relpath, content in files.items():
            out = target / relpath
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(content, encoding="utf-8")
        print(f"wrote {len(files)} golden files to {target.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
