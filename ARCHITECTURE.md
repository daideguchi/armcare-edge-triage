# Architecture

```text
Care inbox messages
        |
        v
Synthetic intake vectorizer
        |
        +--> FP32 single-ticket baseline
        |
        +--> Int8 Arm batch path
                 |
                 v
          Local priority scores
                 |
                 v
          Human review queue
```

## Components

- `scripts/run_arm_benchmark.py`: deterministic dataset generation, baseline inference, optimized inference, metrics, poster asset generation.
- `scripts/verify_outputs.py`: verifies benchmark integrity, claim boundary, artifacts, and secret hygiene.
- `scripts/verify_site.mjs`: opens the dashboard with Playwright and captures a screenshot.
- `site/index.html`: static judge dashboard for the benchmark and triage queue.

## Data Boundary

The demo uses generated care-intake tickets. No patient records, credentials, or external services are required. The output is a routing suggestion for a human operator and does not provide medical advice.

## Optimization Boundary

The benchmark compares a naive float32 one-ticket-at-a-time path against a batched int8 path. The optimized path demonstrates the engineering choices that matter on Arm edge devices: compact weights, compact features, batch execution, and stable local inference.
