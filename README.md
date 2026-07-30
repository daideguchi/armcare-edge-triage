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

> Which incoming messages should a human review first?

Every queue label is an AI routing suggestion over clearly synthetic data. It is not
a verified observation, diagnosis, care decision, or record that support was
performed. The demo never marks an AI suggestion as an action taken.

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

The reported `21.2x` result is an end-to-end comparison between the two named
paths, not a claim that int8 quantization alone provides a `21.2x` speedup. The
optimized path combines batching, int8 storage, integer scoring, and removal of
the baseline probability calculation. See `docs/ROADMAP.md` for the next
benchmark controls needed to isolate each optimization.

The repository also includes a separate, non-publishing ablation runner for
FP32 single-ticket, FP32 batch, INT8 single-ticket, and INT8 batch scoring. It
records warm-ups, every measured run, p50/p95 latency, throughput, accuracy,
agreement with the FP32 single-ticket baseline, architecture, and fixed
numerical-backend thread settings. Each latency run covers the complete
synthetic dataset:

```bash
python3 scripts/run_ablation_benchmark.py \
  --threads 1 --warmup-runs 2 --repeats 7 \
  --require-arm64 --output evidence/ablation_arm64.json
python3 scripts/verify_outputs.py --ablation evidence/ablation_arm64.json
```

The runner refuses to write over the existing public benchmark files. Without
`--output` it only prints JSON. `--require-arm64` exits before writing on other
architectures, so development smoke runs cannot replace the published Arm64
evidence. Output paths must end in `.json`, and an existing non-public artifact
is refused by default; add `--overwrite` only when intentionally replacing that
artifact. The public benchmark files remain protected even with `--overwrite`.

## Reproduce And Validate

Prerequisites are Python 3 with NumPy and Pillow, Node.js, Playwright with a
Chromium browser, and an Arm64 machine. The committed evidence records the exact
Python, NumPy, OS, machine, and processor identifiers used for the measured run.

1. Clone the repository on an Arm64 machine.
2. Review `data/sample_tickets.json` to confirm that only the provided synthetic
   fixtures are used.
3. Regenerate and validate all evidence:

```bash
npm run verify
```

The write path checks the current architecture before benchmarking and refuses
to rewrite the committed public evidence unless the machine reports Arm64.

4. Open `site/index.html` to inspect the local dashboard.

The command writes:

- `evidence/benchmark_latest.json`
- `site/benchmark-inline.js`
- `site/benchmark.json`
- `media/armcare-edge-triage-poster.png`
- `media/site-screenshot.png`

For a read-only integrity check of the committed evidence, without rerunning the
benchmark or rewriting assets:

```bash
python3 scripts/verify_outputs.py
```

## Benchmark Scope And Limitations

- The evidence is a deterministic synthetic separability benchmark, not a
  clinical-quality or real-world accuracy study.
- The current speedup measures the combined production-style routing paths; it
  does not isolate batching from quantization.
- The four-path ablation runner is implemented, but no verified Arm64 ablation
  artifact is committed yet. The existing `21.2x` headline must remain unchanged
  until a new artifact passes strict verification on Arm64.
- Ablation raw runs currently repeat full-dataset inference inside one process;
  separate process-startup variance is not yet measured.
- The memory figure compares resident feature/weight array bytes. It is not
  process peak RSS, energy use, or battery-life measurement.
- The committed measurement was produced on an Apple M4 Arm64 laptop. No result
  is claimed for unmeasured Arm devices.
- No external AI service is called by the benchmark or the static demo.

Known limitations and the prioritized validation plan are maintained in both
this section and `docs/ROADMAP.md`.

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
