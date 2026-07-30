#!/usr/bin/env python3
"""Verify ArmCare benchmark artifacts and claim safety."""

from __future__ import annotations

import argparse
import json
import math
import re
import statistics
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BENCHMARK = ROOT / "evidence" / "benchmark_latest.json"
SITE_JSON = ROOT / "site" / "benchmark.json"
SITE_INLINE = ROOT / "site" / "benchmark-inline.js"
SAMPLE_TICKETS = ROOT / "data" / "sample_tickets.json"
SITE_HTML = ROOT / "site" / "index.html"
POSTER = ROOT / "media" / "armcare-edge-triage-poster.png"
EXPECTED_ABLATION_CLASSES = [
    "urgent_care",
    "access_support",
    "paperwork",
    "routine_followup",
]
EXPECTED_ABLATION_SEED = 260630
MIN_ABLATION_SAMPLES = 12_000
MIN_ABLATION_FEATURES = 192
MIN_ABLATION_REPEATS = 7

SECRET_PATTERNS = [
    re.compile(r"xox[baprs]-", re.I),
    re.compile(r"sk-[A-Za-z0-9_-]{20,}"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"AIza[0-9A-Za-z_-]{20,}"),
]


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def percentile(values: list[float], quantile: float) -> float:
    ordered = sorted(values)
    position = (len(ordered) - 1) * quantile
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    fraction = position - lower
    return ordered[lower] * (1.0 - fraction) + ordered[upper] * fraction


def assert_close(actual: float, expected: float, message: str) -> None:
    assert_true(
        math.isclose(actual, expected, rel_tol=1e-9, abs_tol=1e-9),
        f"{message}: expected {expected}, got {actual}",
    )


def verify_ablation(data: dict[str, object], require_arm64: bool = True) -> None:
    assert_true(data.get("schema_version") == "armcare_ablation_v1", "invalid ablation schema")
    assert_true(data.get("baseline_path") == "fp32_single_ticket", "invalid ablation baseline path")
    assert_true("Synthetic" in str(data.get("claim_boundary", "")), "ablation synthetic boundary missing")
    assert_true("Not medical diagnosis" in str(data.get("claim_boundary", "")), "ablation medical boundary missing")
    assert_true("No external API" in str(data.get("claim_boundary", "")), "ablation external-API boundary missing")

    configuration = data.get("configuration")
    assert_true(isinstance(configuration, dict), "missing ablation configuration")
    samples = configuration.get("samples")
    features = configuration.get("features")
    classes = configuration.get("classes")
    seed = configuration.get("seed")
    warmup_runs = configuration.get("warmup_runs")
    measured_runs = configuration.get("measured_runs")
    threads = configuration.get("threads")
    latency_scope = configuration.get("latency_scope")
    assert_true(
        isinstance(samples, int) and not isinstance(samples, bool) and samples >= MIN_ABLATION_SAMPLES,
        "ablation dataset too small",
    )
    assert_true(
        isinstance(features, int) and not isinstance(features, bool) and features >= MIN_ABLATION_FEATURES,
        "ablation feature count too small",
    )
    assert_true(classes == EXPECTED_ABLATION_CLASSES, "unexpected ablation classes")
    assert_true(seed == EXPECTED_ABLATION_SEED, "unexpected ablation seed")
    assert_true(isinstance(warmup_runs, int) and warmup_runs >= 1, "ablation warm-up missing")
    assert_true(
        isinstance(measured_runs, int) and measured_runs >= MIN_ABLATION_REPEATS,
        "too few ablation raw runs",
    )
    assert_true(isinstance(threads, int) and threads >= 1, "invalid ablation thread count")
    assert_true(
        latency_scope == "milliseconds_per_full_dataset",
        "invalid ablation latency scope",
    )

    platform_data = data.get("platform")
    assert_true(isinstance(platform_data, dict), "missing ablation platform")
    architecture = str(platform_data.get("architecture", "")).lower()
    machine = str(platform_data.get("machine", "")).lower()
    machine_is_arm64 = machine in {"arm64", "aarch64"}
    architecture_is_arm64 = architecture in {"arm64", "aarch64"}
    declared_is_arm64 = platform_data.get("is_arm64")
    assert_true(isinstance(declared_is_arm64, bool), "invalid platform.is_arm64")
    assert_true(
        machine_is_arm64 == architecture_is_arm64,
        "ablation machine and architecture disagree",
    )
    assert_true(
        declared_is_arm64 == (machine_is_arm64 and architecture_is_arm64),
        "platform.is_arm64 disagrees with machine/architecture",
    )
    expected_publication_eligible = (
        declared_is_arm64
        and samples >= MIN_ABLATION_SAMPLES
        and features >= MIN_ABLATION_FEATURES
        and seed == EXPECTED_ABLATION_SEED
        and warmup_runs >= 1
        and measured_runs >= MIN_ABLATION_REPEATS
    )
    assert_true(
        data.get("publication_eligible") is expected_publication_eligible,
        "publication_eligible disagrees with benchmark requirements",
    )
    if require_arm64:
        assert_true(architecture_is_arm64, "ablation architecture is not Arm64")
        assert_true(machine_is_arm64, "ablation machine is not Arm64")
        assert_true(data.get("publication_eligible") is True, "Arm64 ablation is not publication eligible")
    thread_environment = platform_data.get("thread_environment")
    assert_true(isinstance(thread_environment, dict), "missing ablation thread environment")
    expected_thread_keys = {
        "OMP_NUM_THREADS",
        "OPENBLAS_NUM_THREADS",
        "MKL_NUM_THREADS",
        "VECLIB_MAXIMUM_THREADS",
        "NUMEXPR_NUM_THREADS",
    }
    assert_true(set(thread_environment) == expected_thread_keys, "incomplete ablation thread environment")
    assert_true(
        all(value == str(threads) for value in thread_environment.values()),
        "ablation thread environment does not match configured threads",
    )

    paths = data.get("paths")
    assert_true(isinstance(paths, dict), "missing ablation paths")
    expected_paths = {
        "fp32_single_ticket": ("fp32", "single_ticket"),
        "fp32_batch": ("fp32", "batch"),
        "int8_single_ticket": ("int8", "single_ticket"),
        "int8_batch": ("int8", "batch"),
    }
    assert_true(set(paths) == set(expected_paths), "ablation must contain exactly four paths")
    for name, (precision, execution) in expected_paths.items():
        path = paths[name]
        assert_true(isinstance(path, dict), f"invalid ablation path: {name}")
        assert_true(path.get("name") == name, f"path name mismatch: {name}")
        assert_true(path.get("precision") == precision, f"precision mismatch: {name}")
        assert_true(path.get("execution") == execution, f"execution mismatch: {name}")
        assert_true(path.get("warmup_runs") == warmup_runs, f"warm-up mismatch: {name}")
        raw_runs = path.get("raw_runs_ms")
        assert_true(isinstance(raw_runs, list), f"missing raw runs: {name}")
        assert_true(len(raw_runs) == measured_runs, f"raw run count mismatch: {name}")
        assert_true(
            all(isinstance(value, (int, float)) and math.isfinite(value) and value > 0 for value in raw_runs),
            f"invalid raw run latency: {name}",
        )
        expected_p50 = statistics.median(raw_runs)
        expected_p95 = percentile(raw_runs, 0.95)
        assert_close(float(path.get("p50_ms", -1)), expected_p50, f"p50 mismatch: {name}")
        assert_close(float(path.get("p95_ms", -1)), expected_p95, f"p95 mismatch: {name}")
        assert_true(float(path["p95_ms"]) >= float(path["p50_ms"]), f"p95 below p50: {name}")
        expected_throughput = samples / (expected_p50 / 1000.0)
        assert_close(
            float(path.get("throughput_tickets_per_second", -1)),
            expected_throughput,
            f"throughput mismatch: {name}",
        )
        accuracy = path.get("accuracy")
        agreement = path.get("agreement_with_baseline")
        assert_true(isinstance(accuracy, (int, float)) and 0.95 <= accuracy <= 1.0, f"accuracy too low: {name}")
        assert_true(
            isinstance(agreement, (int, float)) and 0.95 <= agreement <= 1.0,
            f"baseline agreement too low: {name}",
        )
    assert_close(
        float(paths["fp32_single_ticket"]["agreement_with_baseline"]),
        1.0,
        "baseline self-agreement mismatch",
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--ablation",
        type=Path,
        help="also strictly verify an Arm64 four-path ablation JSON artifact",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    assert_true(BENCHMARK.exists(), "missing benchmark evidence")
    assert_true(SITE_JSON.exists(), "missing dashboard benchmark JSON")
    assert_true(SITE_INLINE.exists(), "missing inline benchmark data")
    assert_true(SAMPLE_TICKETS.exists(), "missing synthetic sample tickets")
    assert_true(SITE_HTML.exists(), "missing dashboard HTML")
    assert_true(POSTER.exists() and POSTER.stat().st_size > 10_000, "missing poster asset")

    data = json.loads(BENCHMARK.read_text(encoding="utf-8"))
    site_data = json.loads(SITE_JSON.read_text(encoding="utf-8"))
    sample_tickets = json.loads(SAMPLE_TICKETS.read_text(encoding="utf-8"))
    inline_prefix = "window.ARMCARE_BENCHMARK = "
    inline_text = SITE_INLINE.read_text(encoding="utf-8")
    assert_true(inline_text.startswith(inline_prefix), "invalid inline benchmark prefix")
    inline_data = json.loads(inline_text.removeprefix(inline_prefix).removesuffix(";\n"))
    assert_true(site_data == data, "dashboard JSON differs from benchmark evidence")
    assert_true(inline_data == data, "inline dashboard data differs from benchmark evidence")
    assert_true(sample_tickets == data["sample_tickets"], "sample tickets differ from benchmark evidence")

    assert_true(data["platform"]["machine"] in {"arm64", "aarch64"}, "benchmark is not on Arm")
    assert_true(data["dataset"]["samples"] >= 10_000, "dataset too small")
    assert_true(data["baseline"]["accuracy"] >= 0.97, "baseline accuracy too low")
    assert_true(data["optimized"]["accuracy"] >= 0.95, "optimized accuracy too low")
    assert_true(data["optimized"]["agreement_with_baseline"] >= 0.95, "optimized agreement too low")
    assert_true(data["speedup"] >= 3.0, "speedup too low for submission claim")
    assert_true(data["memory"]["reduction_percent"] >= 60.0, "memory reduction too low")
    assert_true("Not medical diagnosis" in data["claim_boundary"], "medical claim boundary missing")
    assert_true("Synthetic" in data["claim_boundary"], "synthetic-data boundary missing")
    assert_true("No external API" in data["claim_boundary"], "external-API boundary missing")

    site_html = SITE_HTML.read_text(encoding="utf-8")
    assert_true("AI routing suggestion" in site_html, "AI suggestion label missing from dashboard")
    assert_true("Human review is required" in site_html, "human-review boundary missing from dashboard")
    assert_true("No support action is recorded" in site_html, "performed-action boundary missing from dashboard")

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

    if args.ablation:
        assert_true(args.ablation.exists(), "missing ablation artifact")
        ablation_data = json.loads(args.ablation.read_text(encoding="utf-8"))
        assert_true(isinstance(ablation_data, dict), "ablation artifact must be a JSON object")
        verify_ablation(ablation_data)

    print(
        "verified: "
        f"speedup={data['speedup']:.2f}x "
        f"optimized_accuracy={data['optimized']['accuracy']:.4f} "
        f"memory_reduction={data['memory']['reduction_percent']:.1f}%"
        + (" ablation=verified" if args.ablation else "")
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
