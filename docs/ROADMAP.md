# Roadmap And Known Limitations

This file records gaps that must not be hidden behind the current benchmark
headline. All future tests must continue to use explicitly synthetic fixtures.

## P0: Isolate The Optimization

The committed `21.2x` result compares the complete
`fp32_single_ticket_probability` path with the complete `int8_arm_batch` path.
It measures a useful application-level change, but it does not attribute the
gain to int8 alone.

The non-publishing runner `scripts/run_ablation_benchmark.py` now measures these
controls:

1. FP32 single-ticket scoring without probability conversion.
2. FP32 batched matrix multiplication.
3. INT8 single-ticket scoring.
4. INT8 batched matrix multiplication.

It preserves warm-up counts, fixed numerical-backend thread settings, raw runs,
p50 and p95 latency, throughput, accuracy, baseline agreement, and architecture
in JSON. Latency is explicitly scoped to one complete synthetic-dataset pass.
`scripts/verify_outputs.py --ablation PATH` strictly checks those fields and
requires an Arm64 artifact.

Remaining stoplines:

- Run the new benchmark on Arm64 and commit an artifact only after strict
  verification. Non-Arm smoke results are not publishable and must not replace
  `evidence/benchmark_latest.json` or its dashboard copies.
- Add repeated fresh-process measurements. Current raw runs repeat
  full-dataset inference inside one process and therefore do not capture Python
  or numerical-backend startup variance.
- Keep the published `21.2x` combined-path claim unchanged until the Arm64
  four-path result exists and has been reviewed.

## P0: Strengthen Arm Evidence

- Record the numerical backend and CPU feature dispatch used by NumPy.
- Capture process peak RSS instead of only array byte counts.
- Add Arm Performix or an equivalent hardware-side measurement when available.
- Measure energy only when a reproducible meter or platform counter is
  available; do not infer battery savings from memory or latency.
- Rerun every published performance claim on Arm64 after benchmark code changes.

## P1: Validate Routing Quality Safely

The current 100% score is produced by a deterministic, separable synthetic
dataset. It does not demonstrate clinical validity or safety.

- Add difficult synthetic boundary cases and out-of-distribution examples.
- Add an explicit `needs_human_confirmation` output for uncertain cases.
- Report per-class precision/recall and abstention behavior.
- Keep facts, observations, AI routing suggestions, and actions actually taken
  as separate record types.
- Do not add diagnosis, emotion probabilities, or disability-based inference.

## P1: Improve Reproducibility

- Declare and lock compatible Python and browser-test dependencies without
  committing dependency directories.
- Add a lightweight CI integrity check that does not overwrite committed Arm
  benchmark evidence.
- Keep the full browser benchmark regeneration as an explicit Arm64 release
  step. The current `--write` path now refuses non-Arm64 machines, but release
  evidence still requires human review before commit.
