# Roadmap And Known Limitations

This file records gaps that must not be hidden behind the current benchmark
headline. All future tests must continue to use explicitly synthetic fixtures.

## P0: Isolate The Optimization

The committed `21.2x` result compares the complete
`fp32_single_ticket_probability` path with the complete `int8_arm_batch` path.
It measures a useful application-level change, but it does not attribute the
gain to int8 alone.

On the same Arm64 device, add and record these controls:

1. FP32 single-ticket scoring without probability conversion.
2. FP32 batched matrix multiplication.
3. INT8 single-ticket scoring.
4. INT8 batched matrix multiplication.

Use warm-up runs, fixed thread counts, p50 and p95 latency, throughput, output
agreement, and repeated process-level runs. Preserve raw run values in JSON.

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
  step.
