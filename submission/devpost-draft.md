# ArmCare Edge Triage

## Elevator Pitch

ArmCare Edge Triage helps small clinics, disability support offices, and community care teams triage sensitive intake messages on an Arm device without sending private text to a cloud AI system.

## The Problem

Front offices receive urgent symptoms, accessibility needs, paperwork requests, and routine scheduling messages in the same queue. The people reviewing those queues are often overloaded, and the first problem is not diagnosis. The first problem is review ordering: which messages should a human inspect first and which requests may require accommodation support.

## What It Does

The app runs a local AI priority classifier over generated care-intake messages. It routes each message into one of four human-review queues:

- urgent care
- access support
- paperwork
- routine follow-up

The dashboard shows live benchmark proof from the current machine: Arm platform, dataset size, latency, speedup, accuracy, and memory reduction.

Challenge track fit: Mobile AI / on-device edge AI. The project is designed around local inference on Arm-powered devices rather than cloud-only AI.

## How AI Is Used

ArmCare uses a compact local classifier to turn each intake message into a route. The AI is not a medical decision-maker and does not provide a diagnosis. It is an operational sorter that gives staff a prioritized review queue.

Each output is stored and displayed as an AI routing suggestion. It is not a
verified observation and is never recorded as support that was actually
performed.

## Arm Optimization

The repository compares two local inference paths:

- `fp32_single_ticket`: a naive float32 baseline that processes one ticket at a time.
- `int8_arm_batch`: a quantized batch path designed for Arm edge devices.

The optimized path applies int8 quantization and batch matrix multiplication to reduce memory pressure and latency. `npm run verify` regenerates the benchmark and writes `evidence/benchmark_latest.json`, so the submission claim is reproducible instead of hand-written.

On an Apple M4 Arm64 run, the complete optimized route was `21.2x` faster and
used 75.0% fewer feature/weight array bytes than the complete baseline route.
This is deliberately described as an end-to-end path comparison: it combines
batching, int8 storage, integer scoring, and removal of the baseline probability
calculation. It is not presented as an int8-only speedup. Raw run values,
platform identifiers, agreement, and deterministic seed are committed in the
evidence JSON.

## Why It Matters

Care teams need AI that is fast, cheap, private, and understandable. Arm devices are already in clinics, laptops, tablets, and phones. A local triage layer can help teams respond faster while keeping sensitive intake text under local control.

For developers, the reusable output is a compact benchmark harness with a
baseline/optimized path, deterministic fixtures, machine-readable evidence,
claim checks, and a static judge dashboard. The same structure can be adapted
to other local classification workloads without using care records.

## Built With

- Python
- NumPy
- Pillow
- Playwright
- Static HTML/CSS/JavaScript
- Arm64 macOS benchmark hardware

## Submission Links To Add

- Public repository: https://github.com/daideguchi/armcare-edge-triage
- Live demo: https://daideguchi.github.io/armcare-edge-triage/
- Demo video: https://youtu.be/3M4srfq2kCs

## Claim Boundary

This project uses synthetic care-intake data. It is not medical diagnosis, not patient-risk scoring, and not a replacement for professional judgment.

The 100% synthetic benchmark score is not a real-world or clinical accuracy
claim. Memory results are array byte counts, not measured energy use or battery
life.
