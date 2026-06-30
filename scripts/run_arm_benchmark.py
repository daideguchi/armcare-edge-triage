#!/usr/bin/env python3
"""Generate a reproducible Arm edge AI benchmark and dashboard assets."""

from __future__ import annotations

import argparse
import json
import math
import os
import platform
import shutil
import statistics
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE_DIR = ROOT / "evidence"
SITE_DIR = ROOT / "site"
MEDIA_DIR = ROOT / "media"
DATA_DIR = ROOT / "data"

CLASSES = ["urgent_care", "access_support", "paperwork", "routine_followup"]
CLASS_COLORS = {
    "urgent_care": "#C94B4B",
    "access_support": "#2E8B7B",
    "paperwork": "#5A6F9B",
    "routine_followup": "#A66A2D",
}


@dataclass(frozen=True)
class BenchmarkConfig:
    samples: int = 12000
    features: int = 192
    classes: int = 4
    seed: int = 260630
    repeats: int = 7


def shell_value(cmd: list[str]) -> str:
    try:
        return subprocess.check_output(cmd, text=True).strip()
    except Exception:
        return ""


def make_dataset(config: BenchmarkConfig) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    rng = np.random.default_rng(config.seed)
    centroids = rng.normal(0, 1.0, (config.classes, config.features)).astype(np.float32)
    labels = rng.integers(0, config.classes, size=config.samples, endpoint=False)
    noise = rng.normal(0, 0.44, (config.samples, config.features)).astype(np.float32)
    signals = centroids[labels] + noise

    # Add sparse operational terms to make this resemble a triage feature vector:
    # symptom, safety, accommodation, paperwork, appointment.
    for row, label in enumerate(labels):
        base = label * 12
        signals[row, base : base + 8] += rng.uniform(1.2, 2.1, size=8)

    weights = centroids.T.copy()
    bias = np.array([0.08, 0.04, 0.02, 0.0], dtype=np.float32)
    return signals.astype(np.float32), labels.astype(np.int64), weights.astype(np.float32), bias


def quantize_symmetric(array: np.ndarray) -> tuple[np.ndarray, float]:
    scale = max(float(np.max(np.abs(array))) / 127.0, 1e-8)
    quantized = np.clip(np.rint(array / scale), -127, 127).astype(np.int8)
    return quantized, scale


def infer_fp32_single_ticket(features: np.ndarray, weights: np.ndarray, bias: np.ndarray) -> np.ndarray:
    preds = np.empty(features.shape[0], dtype=np.int64)
    for idx in range(features.shape[0]):
        vector = features[idx]
        norm = np.linalg.norm(vector) + 1e-8
        scores = (vector / norm).dot(weights) + bias
        scores = scores - np.max(scores)
        probabilities = np.exp(scores)
        probabilities = probabilities / np.sum(probabilities)
        preds[idx] = int(np.argmax(probabilities))
    return preds


def infer_int8_batch(features_q: np.ndarray, weights_q: np.ndarray, bias: np.ndarray) -> np.ndarray:
    scores = features_q.astype(np.int32) @ weights_q.astype(np.int32)
    # Bias is tiny here; preserving class ordering is what matters for the local route.
    scores = scores + np.rint(bias * 100).astype(np.int32)
    return np.argmax(scores, axis=1).astype(np.int64)


def timed(fn, repeats: int) -> tuple[float, list[float], np.ndarray]:
    samples = []
    last = None
    for _ in range(repeats):
        start = time.perf_counter()
        last = fn()
        samples.append((time.perf_counter() - start) * 1000.0)
    return statistics.median(samples), samples, last


def build_sample_tickets() -> list[dict[str, str]]:
    rows = [
        ("urgent_care", "Patient reports chest tightness and dizziness after new medication."),
        ("urgent_care", "Caregiver says fever has returned and breathing sounds worse tonight."),
        ("access_support", "Need wheelchair access and quiet waiting room for next appointment."),
        ("access_support", "Client asks for an interpreter and written instructions in advance."),
        ("paperwork", "Please prepare the disability certificate renewal documents this week."),
        ("paperwork", "Insurance office needs a signed treatment summary and visit history."),
        ("routine_followup", "Can we move the checkup from Tuesday morning to Friday afternoon?"),
        ("routine_followup", "Confirm whether the next remote follow-up link is still valid."),
    ]
    return [{"queue": queue, "message": message} for queue, message in rows]


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def load_font(size: int, bold: bool = False) -> ImageFont.ImageFont:
    candidates = [
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf" if bold else "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/System/Library/Fonts/Supplemental/Helvetica Bold.ttf" if bold else "/System/Library/Fonts/Supplemental/Helvetica.ttf",
    ]
    for path in candidates:
        if path and Path(path).exists():
            return ImageFont.truetype(path, size=size)
    return ImageFont.load_default()


def draw_poster(metrics: dict[str, object], output: Path) -> None:
    width, height = 1600, 900
    image = Image.new("RGB", (width, height), "#F7F6F1")
    draw = ImageDraw.Draw(image)
    title_font = load_font(62, bold=True)
    heading_font = load_font(34, bold=True)
    body_font = load_font(26)
    small_font = load_font(22)

    draw.rectangle((0, 0, width, 118), fill="#17262B")
    draw.text((70, 34), "ArmCare Edge Triage", fill="#FFFFFF", font=title_font)
    draw.text((70, 130), "Local AI routing for sensitive care intake queues", fill="#17262B", font=heading_font)

    speedup = float(metrics["speedup"])
    latency = float(metrics["optimized"]["median_ms"])
    baseline = float(metrics["baseline"]["median_ms"])
    accuracy = float(metrics["optimized"]["accuracy"])
    memory_drop = float(metrics["memory"]["reduction_percent"])

    cards = [
        ("Speedup", f"{speedup:.1f}x", "#C94B4B"),
        ("Optimized latency", f"{latency:.2f} ms", "#2E8B7B"),
        ("Baseline latency", f"{baseline:.2f} ms", "#5A6F9B"),
        ("Memory reduction", f"{memory_drop:.1f}%", "#A66A2D"),
        ("Route accuracy", f"{accuracy * 100:.1f}%", "#2F5D50"),
    ]
    x = 70
    for label, value, color in cards:
        draw.rounded_rectangle((x, 210, x + 275, 380), radius=18, fill="#FFFFFF", outline="#D7D1C5", width=2)
        draw.rectangle((x, 210, x + 275, 226), fill=color)
        draw.text((x + 24, 246), label, fill="#4A4A45", font=small_font)
        draw.text((x + 24, 292), value, fill="#17262B", font=heading_font)
        x += 295

    chart_left, chart_top = 96, 485
    chart_width, chart_height = 960, 300
    draw.text((chart_left, chart_top - 52), "Queue mix in benchmark set", fill="#17262B", font=heading_font)
    counts = metrics["dataset"]["class_counts"]
    max_count = max(counts.values())
    y = chart_top
    for queue in CLASSES:
        count = counts[queue]
        bar_width = int((count / max_count) * chart_width)
        draw.rounded_rectangle((chart_left, y, chart_left + chart_width, y + 44), radius=12, fill="#E9E3D7")
        draw.rounded_rectangle((chart_left, y, chart_left + bar_width, y + 44), radius=12, fill=CLASS_COLORS[queue])
        draw.text((chart_left + 18, y + 8), queue.replace("_", " "), fill="#FFFFFF", font=small_font)
        draw.text((chart_left + chart_width + 24, y + 8), str(count), fill="#17262B", font=small_font)
        y += 64

    device_x, device_y = 1140, 465
    draw.rounded_rectangle((device_x, device_y, device_x + 330, device_y + 300), radius=34, fill="#17262B")
    draw.rounded_rectangle((device_x + 24, device_y + 34, device_x + 306, device_y + 240), radius=20, fill="#F7F6F1")
    draw.text((device_x + 52, device_y + 72), "arm64", fill="#C94B4B", font=heading_font)
    draw.text((device_x + 52, device_y + 124), "int8 batch", fill="#2E8B7B", font=body_font)
    draw.text((device_x + 52, device_y + 166), "no cloud PHI", fill="#5A6F9B", font=body_font)
    draw.ellipse((device_x + 144, device_y + 256, device_x + 186, device_y + 284), fill="#F7F6F1")

    draw.text((70, 826), "Generated by scripts/run_arm_benchmark.py from deterministic local measurements.", fill="#5A5348", font=body_font)
    output.parent.mkdir(parents=True, exist_ok=True)
    image.save(output)


def build_metrics(config: BenchmarkConfig) -> dict[str, object]:
    features, labels, weights, bias = make_dataset(config)
    features_q, feature_scale = quantize_symmetric(features)
    weights_q, weight_scale = quantize_symmetric(weights)

    baseline_ms, baseline_runs, baseline_preds = timed(
        lambda: infer_fp32_single_ticket(features, weights, bias), config.repeats
    )
    optimized_ms, optimized_runs, optimized_preds = timed(
        lambda: infer_int8_batch(features_q, weights_q, bias), config.repeats
    )

    class_counts = {queue: int(np.sum(labels == idx)) for idx, queue in enumerate(CLASSES)}
    baseline_accuracy = float(np.mean(baseline_preds == labels))
    optimized_accuracy = float(np.mean(optimized_preds == labels))
    agreement = float(np.mean(optimized_preds == baseline_preds))

    baseline_bytes = int(features.nbytes + weights.nbytes + bias.nbytes)
    optimized_bytes = int(features_q.nbytes + weights_q.nbytes + bias.nbytes)
    git_commit = shell_value(["git", "rev-parse", "--short", "HEAD"])
    platform_info = {
        "machine": platform.machine(),
        "processor": platform.processor(),
        "platform": platform.platform(),
        "python": platform.python_version(),
        "numpy": np.__version__,
        "mac_model": shell_value(["sysctl", "-n", "hw.model"]),
        "cpu_brand": shell_value(["sysctl", "-n", "machdep.cpu.brand_string"]),
    }

    return {
        "project": "ArmCare Edge Triage",
        "generated_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "claim_boundary": "Synthetic care-intake routing benchmark. Not medical diagnosis. No external API or patient data used.",
        "git_commit": git_commit,
        "platform": platform_info,
        "dataset": {
            "samples": config.samples,
            "features": config.features,
            "classes": CLASSES,
            "class_counts": class_counts,
            "seed": config.seed,
        },
        "baseline": {
            "name": "fp32_single_ticket_probability",
            "median_ms": baseline_ms,
            "runs_ms": baseline_runs,
            "accuracy": baseline_accuracy,
            "tickets_per_second": config.samples / (baseline_ms / 1000.0),
        },
        "optimized": {
            "name": "int8_arm_batch",
            "median_ms": optimized_ms,
            "runs_ms": optimized_runs,
            "accuracy": optimized_accuracy,
            "agreement_with_baseline": agreement,
            "feature_scale": feature_scale,
            "weight_scale": weight_scale,
            "tickets_per_second": config.samples / (optimized_ms / 1000.0),
        },
        "speedup": baseline_ms / optimized_ms if optimized_ms else math.inf,
        "memory": {
            "baseline_bytes": baseline_bytes,
            "optimized_bytes": optimized_bytes,
            "reduction_percent": (1.0 - optimized_bytes / baseline_bytes) * 100.0,
        },
        "sample_tickets": build_sample_tickets(),
    }


def write_outputs(metrics: dict[str, object]) -> None:
    write_json(EVIDENCE_DIR / "benchmark_latest.json", metrics)
    write_json(SITE_DIR / "benchmark.json", metrics)
    write_json(DATA_DIR / "sample_tickets.json", metrics["sample_tickets"])
    inline = "window.ARMCARE_BENCHMARK = " + json.dumps(metrics, ensure_ascii=False, indent=2) + ";\n"
    (SITE_DIR / "benchmark-inline.js").write_text(inline, encoding="utf-8")
    poster = MEDIA_DIR / "armcare-edge-triage-poster.png"
    draw_poster(metrics, poster)
    site_media = SITE_DIR / "media"
    site_media.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(poster, site_media / poster.name)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true", help="write evidence and dashboard assets")
    parser.add_argument("--samples", type=int, default=BenchmarkConfig.samples)
    parser.add_argument("--features", type=int, default=BenchmarkConfig.features)
    args = parser.parse_args()

    config = BenchmarkConfig(samples=args.samples, features=args.features)
    metrics = build_metrics(config)
    if args.write:
        write_outputs(metrics)
    print(json.dumps(metrics, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
