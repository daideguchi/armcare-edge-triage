# Demo Script

## 0:00 - Problem

Small care teams receive urgent symptoms, access requests, paperwork, and routine follow-ups in the same inbox. Manual sorting is slow, and sending sensitive intake text to a cloud model is often not acceptable.

## 0:20 - Product

ArmCare Edge Triage runs a local AI route classifier. It sorts each message into urgent care, access support, paperwork, or routine follow-up.

## 0:45 - Arm Optimization

The benchmark compares a float32 single-ticket baseline with an int8 batched path. The optimized path is built for Arm edge devices: smaller memory, lower latency, and reproducible local inference.

## 1:15 - Proof

Run `npm run verify`. The script regenerates the benchmark, writes JSON evidence, creates the poster asset, verifies the dashboard, and captures a screenshot.

## 1:45 - Impact

This is not a medical diagnosis system. It is a privacy-preserving operational queue that helps staff find messages that need immediate review.

## 2:10 - Close

ArmCare shows how Arm edge AI can be useful beyond model demos: local, measured, and tied to a real workflow where speed and privacy both matter.
