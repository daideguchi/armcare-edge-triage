# ArmCare Edge Triage

ArmCare Edge Triage is an on-device AI triage desk for small clinics, disability support offices, and community care teams that receive more inbound requests than staff can safely review in real time.

The problem is concrete: urgent care signals are mixed into routine paperwork, access requests, and scheduling questions. Many teams cannot send sensitive intake text to a cloud model by default, and slow manual sorting delays the first response.

This project uses AI as a local priority classifier. It turns each intake message into a compact feature vector, classifies it into an operational queue, and produces a human-readable routing packet. The optimization work is focused on Arm devices: batching, int8 quantization, lower memory footprint, and reproducible latency measurements on `arm64`.

## Challenge Fit

- Target challenge: Arm Create: AI Optimization Challenge.
- Track direction: practical edge AI optimization on Arm hardware.
- Hardware proof: the benchmark records `platform.machine()` and `platform.platform()` in `evidence/benchmark_latest.json`.
- No external API requirement: all scoring and UI proof run locally.
- Claim boundary: this is a reproducible edge optimization demo, not a clinical diagnosis system.

## What It Solves

ArmCare helps a small front office answer one question quickly:

> Which incoming messages need immediate human attention, and which can safely wait in a normal workflow?

It prioritizes four queues:

- `urgent_care`: symptoms, safety, medication, escalation.
- `access_support`: accessibility, interpreter, mobility, disability accommodation.
- `paperwork`: forms, certificates, insurance, benefits documentation.
- `routine_followup`: appointments, reminders, non-urgent status checks.

## AI And Arm Optimization

The repository contains two measured inference paths:

- `fp32_single_ticket`: float32 inference executed one ticket at a time.
- `int8_arm_batch`: quantized int8 inference executed as a fused batch.

The optimized path is designed for Arm edge devices where memory bandwidth and battery matter. It uses a compact int8 representation for the message features and classifier weights, then performs batched matrix multiplication with deterministic output.

Run:

```bash
npm run verify
```

Outputs:

- `evidence/benchmark_latest.json`
- `site/benchmark-inline.js`
- `site/benchmark.json`
- `media/armcare-edge-triage-poster.png`
- `media/site-screenshot.png`

## Local Demo

Open `site/index.html` in a browser. It renders the current benchmark, queue distribution, and the live claim boundary from the generated JSON.

Public demo: https://daideguchi.github.io/armcare-edge-triage/

Public repository: https://github.com/daideguchi/armcare-edge-triage

Demo video: https://youtu.be/3M4srfq2kCs

## Submission Assets

- Devpost draft: `submission/devpost-draft.md`
- Demo script: `submission/demo-script.md`
- Demo video: `submission/demo-video-build/armcare-edge-triage-demo.mp4`
- YouTube thumbnail: `submission/youtube-thumbnail.png`
- Architecture: `ARCHITECTURE.md`
- Visual asset: `media/armcare-edge-triage-poster.png`

## License

MIT. See `LICENSE`.
