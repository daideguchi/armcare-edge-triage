# ArmCare Edge Triage

## Elevator Pitch

ArmCare Edge Triage helps small clinics, disability support offices, and community care teams triage sensitive intake messages on an Arm device without sending private text to a cloud AI system.

## The Problem

Front offices receive urgent symptoms, accessibility needs, paperwork requests, and routine scheduling messages in the same queue. The people reviewing those queues are often overloaded, and the first problem is not diagnosis. The first problem is safe routing: who needs a human right now, which requests require accommodation support, and which messages can follow the normal workflow.

## What It Does

The app runs a local AI priority classifier over generated care-intake messages. It routes each message into one of four human-review queues:

- urgent care
- access support
- paperwork
- routine follow-up

The dashboard shows live benchmark proof from the current machine: Arm platform, dataset size, latency, speedup, accuracy, and memory reduction.

## How AI Is Used

ArmCare uses a compact local classifier to turn each intake message into a route. The AI is not a medical decision-maker and does not provide a diagnosis. It is an operational sorter that gives staff a prioritized review queue.

## Arm Optimization

The repository compares two local inference paths:

- `fp32_single_ticket`: a naive float32 baseline that processes one ticket at a time.
- `int8_arm_batch`: a quantized batch path designed for Arm edge devices.

The optimized path applies int8 quantization and batch matrix multiplication to reduce memory pressure and latency. `npm run verify` regenerates the benchmark and writes `evidence/benchmark_latest.json`, so the submission claim is reproducible instead of hand-written.

## Why It Matters

Care teams need AI that is fast, cheap, private, and understandable. Arm devices are already in clinics, laptops, tablets, and phones. A local triage layer can help teams respond faster while keeping sensitive intake text under local control.

## Built With

- Python
- NumPy
- Pillow
- Playwright
- Static HTML/CSS/JavaScript
- Arm64 macOS benchmark hardware

## Submission Links To Add

- Public repository:
- Live demo:
- Demo video:

## Claim Boundary

This project uses synthetic care-intake data. It is not medical diagnosis, not patient-risk scoring, and not a replacement for professional judgment.
