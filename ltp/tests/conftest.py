from __future__ import annotations

from pathlib import Path

FIXTURES = Path(__file__).resolve().parents[1] / "evals" / "fixtures"
GOLDEN = Path(__file__).resolve().parent / "golden"


def fixture_cases(kind: str):
    directory = FIXTURES / kind
    return sorted(p for p in directory.iterdir() if (p / "ltp-model.yaml").exists())
