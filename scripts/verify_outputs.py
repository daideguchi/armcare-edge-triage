#!/usr/bin/env python3
"""Verify ArmCare benchmark artifacts and claim safety."""

from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BENCHMARK = ROOT / "evidence" / "benchmark_latest.json"
SITE_INLINE = ROOT / "site" / "benchmark-inline.js"
POSTER = ROOT / "media" / "armcare-edge-triage-poster.png"

SECRET_PATTERNS = [
    re.compile(r"xox[baprs]-", re.I),
    re.compile(r"sk-[A-Za-z0-9_-]{20,}"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"AIza[0-9A-Za-z_-]{20,}"),
]


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> int:
    assert_true(BENCHMARK.exists(), "missing benchmark evidence")
    assert_true(SITE_INLINE.exists(), "missing inline benchmark data")
    assert_true(POSTER.exists() and POSTER.stat().st_size > 10_000, "missing poster asset")

    data = json.loads(BENCHMARK.read_text(encoding="utf-8"))
    assert_true(data["platform"]["machine"] in {"arm64", "aarch64"}, "benchmark is not on Arm")
    assert_true(data["dataset"]["samples"] >= 10_000, "dataset too small")
    assert_true(data["baseline"]["accuracy"] >= 0.97, "baseline accuracy too low")
    assert_true(data["optimized"]["accuracy"] >= 0.95, "optimized accuracy too low")
    assert_true(data["optimized"]["agreement_with_baseline"] >= 0.95, "optimized agreement too low")
    assert_true(data["speedup"] >= 3.0, "speedup too low for submission claim")
    assert_true(data["memory"]["reduction_percent"] >= 60.0, "memory reduction too low")
    assert_true("Not medical diagnosis" in data["claim_boundary"], "medical claim boundary missing")

    checked_files = [
        ROOT / "README.md",
        ROOT / "ARCHITECTURE.md",
        ROOT / "submission" / "devpost-draft.md",
        ROOT / "site" / "index.html",
        ROOT / "site" / "app.js",
        BENCHMARK,
    ]
    for path in checked_files:
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        for pattern in SECRET_PATTERNS:
            assert_true(not pattern.search(text), f"possible secret in {path}")

    print(
        "verified: "
        f"speedup={data['speedup']:.2f}x "
        f"optimized_accuracy={data['optimized']['accuracy']:.4f} "
        f"memory_reduction={data['memory']['reduction_percent']:.1f}%"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
