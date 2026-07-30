#!/usr/bin/env python3
"""Measure four isolated ArmCare scoring paths without rewriting public evidence."""

from __future__ import annotations

import argparse
import json
import math
import os
import platform
import subprocess
import sys
import time
from pathlib import Path
from typing import Callable


def _requested_threads(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--threads", type=int, default=1)
    args, _ = parser.parse_known_args(argv)
    if args.threads < 1:
        raise SystemExit("--threads must be at least 1")
    return args.threads


# Numerical backends read these variables when NumPy is imported. Set every
# supported backend to the same value before importing NumPy or benchmark code.
THREADS = _requested_threads(sys.argv[1:])
THREAD_ENV_KEYS = (
    "OMP_NUM_THREADS",
    "OPENBLAS_NUM_THREADS",
    "MKL_NUM_THREADS",
    "VECLIB_MAXIMUM_THREADS",
    "NUMEXPR_NUM_THREADS",
)
for _key in THREAD_ENV_KEYS:
    os.environ[_key] = str(THREADS)

import numpy as np  # noqa: E402

from run_arm_benchmark import (  # noqa: E402
    CLASSES,
    BenchmarkConfig,
    make_dataset,
    quantize_symmetric,
)


ROOT = Path(__file__).resolve().parents[1]
PUBLIC_ARTIFACTS = {
    (ROOT / "evidence" / "benchmark_latest.json").resolve(),
    (ROOT / "site" / "benchmark.json").resolve(),
    (ROOT / "site" / "benchmark-inline.js").resolve(),
}


def shell_value(cmd: list[str]) -> str:
    try:
        return subprocess.check_output(cmd, text=True, stderr=subprocess.DEVNULL).strip()
    except Exception:
        return ""


def infer_fp32_single(features: np.ndarray, weights: np.ndarray, bias: np.ndarray) -> np.ndarray:
    predictions = np.empty(features.shape[0], dtype=np.int64)
    for index, vector in enumerate(features):
        predictions[index] = int(np.argmax(vector.dot(weights) + bias))
    return predictions


def infer_fp32_batch(features: np.ndarray, weights: np.ndarray, bias: np.ndarray) -> np.ndarray:
    return np.argmax(features @ weights + bias, axis=1).astype(np.int64)


def infer_int8_single(features: np.ndarray, weights: np.ndarray, bias: np.ndarray) -> np.ndarray:
    predictions = np.empty(features.shape[0], dtype=np.int64)
    bias_i32 = np.rint(bias * 100).astype(np.int32)
    weights_i32 = weights.astype(np.int32)
    for index, vector in enumerate(features):
        predictions[index] = int(np.argmax(vector.astype(np.int32).dot(weights_i32) + bias_i32))
    return predictions


def infer_int8_batch(features: np.ndarray, weights: np.ndarray, bias: np.ndarray) -> np.ndarray:
    scores = features.astype(np.int32) @ weights.astype(np.int32)
    scores += np.rint(bias * 100).astype(np.int32)
    return np.argmax(scores, axis=1).astype(np.int64)


def percentile(values: list[float], quantile: float) -> float:
    ordered = sorted(values)
    position = (len(ordered) - 1) * quantile
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    fraction = position - lower
    return ordered[lower] * (1.0 - fraction) + ordered[upper] * fraction


def measure_path(
    name: str,
    precision: str,
    execution: str,
    fn: Callable[[], np.ndarray],
    labels: np.ndarray,
    baseline_predictions: np.ndarray,
    samples: int,
    warmup_runs: int,
    measured_runs: int,
) -> dict[str, object]:
    for _ in range(warmup_runs):
        fn()

    raw_runs_ms: list[float] = []
    predictions = np.empty(0, dtype=np.int64)
    for _ in range(measured_runs):
        started = time.perf_counter()
        predictions = fn()
        raw_runs_ms.append((time.perf_counter() - started) * 1000.0)

    p50_ms = percentile(raw_runs_ms, 0.50)
    p95_ms = percentile(raw_runs_ms, 0.95)
    return {
        "name": name,
        "precision": precision,
        "execution": execution,
        "warmup_runs": warmup_runs,
        "raw_runs_ms": raw_runs_ms,
        "p50_ms": p50_ms,
        "p95_ms": p95_ms,
        "throughput_tickets_per_second": samples / (p50_ms / 1000.0),
        "accuracy": float(np.mean(predictions == labels)),
        "agreement_with_baseline": float(np.mean(predictions == baseline_predictions)),
    }


def build_ablation(
    samples: int,
    features_count: int,
    seed: int,
    warmup_runs: int,
    measured_runs: int,
) -> dict[str, object]:
    config = BenchmarkConfig(
        samples=samples,
        features=features_count,
        seed=seed,
        repeats=measured_runs,
    )
    features, labels, weights, bias = make_dataset(config)
    features_q, feature_scale = quantize_symmetric(features)
    weights_q, weight_scale = quantize_symmetric(weights)

    functions: dict[str, tuple[str, str, Callable[[], np.ndarray]]] = {
        "fp32_single_ticket": (
            "fp32",
            "single_ticket",
            lambda: infer_fp32_single(features, weights, bias),
        ),
        "fp32_batch": (
            "fp32",
            "batch",
            lambda: infer_fp32_batch(features, weights, bias),
        ),
        "int8_single_ticket": (
            "int8",
            "single_ticket",
            lambda: infer_int8_single(features_q, weights_q, bias),
        ),
        "int8_batch": (
            "int8",
            "batch",
            lambda: infer_int8_batch(features_q, weights_q, bias),
        ),
    }
    baseline_predictions = functions["fp32_single_ticket"][2]()
    paths = {
        name: measure_path(
            name=name,
            precision=precision,
            execution=execution,
            fn=fn,
            labels=labels,
            baseline_predictions=baseline_predictions,
            samples=samples,
            warmup_runs=warmup_runs,
            measured_runs=measured_runs,
        )
        for name, (precision, execution, fn) in functions.items()
    }

    machine = platform.machine()
    normalized_arch = machine.lower()
    is_arm64 = normalized_arch in {"arm64", "aarch64"}
    publication_eligible = (
        is_arm64
        and samples >= BenchmarkConfig.samples
        and features_count >= BenchmarkConfig.features
        and seed == BenchmarkConfig.seed
        and warmup_runs >= 1
        and measured_runs >= BenchmarkConfig.repeats
    )
    return {
        "schema_version": "armcare_ablation_v1",
        "project": "ArmCare Edge Triage",
        "generated_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "claim_boundary": (
            "Synthetic care-intake routing benchmark. Not medical diagnosis. "
            "No external API or patient data used."
        ),
        "publication_eligible": publication_eligible,
        "git_commit": shell_value(["git", "-C", str(ROOT), "rev-parse", "--short", "HEAD"]),
        "configuration": {
            "samples": samples,
            "features": features_count,
            "classes": CLASSES,
            "seed": seed,
            "warmup_runs": warmup_runs,
            "measured_runs": measured_runs,
            "threads": THREADS,
            "latency_scope": "milliseconds_per_full_dataset",
        },
        "platform": {
            "machine": machine,
            "architecture": normalized_arch,
            "processor": platform.processor(),
            "platform": platform.platform(),
            "python": platform.python_version(),
            "numpy": np.__version__,
            "is_arm64": is_arm64,
            "thread_environment": {key: os.environ[key] for key in THREAD_ENV_KEYS},
        },
        "quantization": {
            "feature_scale": feature_scale,
            "weight_scale": weight_scale,
        },
        "baseline_path": "fp32_single_ticket",
        "paths": paths,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--samples", type=int, default=BenchmarkConfig.samples)
    parser.add_argument("--features", type=int, default=BenchmarkConfig.features)
    parser.add_argument("--seed", type=int, default=BenchmarkConfig.seed)
    parser.add_argument("--warmup-runs", type=int, default=2)
    parser.add_argument("--repeats", type=int, default=7)
    parser.add_argument("--threads", type=int, default=THREADS)
    parser.add_argument(
        "--output",
        type=Path,
        help="optional ablation JSON path; public benchmark paths are always refused",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="replace an existing non-public ablation JSON output",
    )
    parser.add_argument(
        "--require-arm64",
        action="store_true",
        help="exit without writing when the current machine is not Arm64",
    )
    args = parser.parse_args()
    if args.samples < 1 or args.features < 48:
        parser.error("--samples must be positive and --features must be at least 48")
    if args.warmup_runs < 1 or args.repeats < 3:
        parser.error("--warmup-runs must be at least 1 and --repeats at least 3")
    return args


def main() -> int:
    args = parse_args()
    payload = build_ablation(
        samples=args.samples,
        features_count=args.features,
        seed=args.seed,
        warmup_runs=args.warmup_runs,
        measured_runs=args.repeats,
    )
    if args.require_arm64 and not payload["platform"]["is_arm64"]:
        print("Arm64 is required; no artifact was written.", file=sys.stderr)
        return 2
    if args.output:
        output = args.output.resolve()
        if output.suffix.lower() != ".json":
            print(f"ablation output must use a .json extension: {output}", file=sys.stderr)
            return 2
        if output in PUBLIC_ARTIFACTS:
            print(f"refusing to overwrite public benchmark artifact: {output}", file=sys.stderr)
            return 2
        if output.exists() and not args.overwrite:
            print(
                f"refusing to overwrite existing output without --overwrite: {output}",
                file=sys.stderr,
            )
            return 2
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
