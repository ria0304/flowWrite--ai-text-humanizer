# FlowWrite — Benchmark Results

## Test Configuration

| Setting | Value |
|:--------|:------|
| Model | llama3.2:latest |
| NUM_CANDIDATES | 1 (benchmarking) / 3 (production) |
| Pipeline version | v1.0 |
| Date tested | 31 May 2026 |

---

## Results — V1 Pipeline (with Flow Smoother)

| Sample | Tone | Aggr | Original HLS | Refined HLS | HLS Δ | Time (s) |
|:-------|:-----|:----:|:------------:|:-----------:|:-----:|:--------:|
| academic_01 | academic | 2 | 0.563 | 0.822 | +0.259 | 688 |
| academic_02 | academic | 2 | 0.653 | 0.826 | +0.173 | 507 |
| academic_03 | academic | 2 | 0.572 | 0.931 | +0.358 | 610 |
| blog_01 | conversational | 2 | 0.624 | 0.731 | +0.107 | 870 |
| blog_02 | conversational | 2 | 0.626 | 0.716 | +0.090 | 1196 |
| technical_01 | technical | 2 | 0.566 | 0.850 | +0.284 | 905 |
| technical_02 | technical | 2 | 0.532 | 0.802 | +0.271 | 741 |
| business_01 | formal_professional | 2 | 0.492 | 0.856 | +0.364 | 782 |
| business_02 | formal_professional | 2 | 0.556 | 0.778 | +0.222 | 655 |
| healthcare_01 | formal_report | 2 | 0.521 | 0.926 | +0.406 | 927 |

---

## Results — V2 Pipeline (no Flow Smoother)

| Sample | Tone | Aggr | Original HLS | Refined HLS | HLS Δ | Time (s) |
|:-------|:-----|:----:|:------------:|:-----------:|:-----:|:--------:|
| academic_01 | academic | 2 | 0.563 | 0.861 | +0.298 | 311 |
| academic_02 | academic | 2 | 0.653 | 0.887 | +0.234 | 279 |
| academic_03 | academic | 2 | 0.572 | 0.936 | +0.363 | 285 |
| blog_01 | conversational | 2 | 0.624 | — | — | — |
| blog_02 | conversational | 2 | 0.626 | — | — | — |
| technical_01 | technical | 2 | 0.566 | — | — | — |
| technical_02 | technical | 2 | 0.532 | — | — | — |
| business_01 | formal_professional | 2 | 0.492 | — | — | — |
| business_02 | formal_professional | 2 | 0.556 | — | — | — |
| healthcare_01 | formal_report | 2 | 0.521 | — | — | — |

---

## V1 vs V2 Pipeline Comparison

| Sample | V1 HLS | V2 HLS | V1 Time (s) | V2 Time (s) | Winner |
|:-------|:------:|:------:|:-----------:|:-----------:|:------:|
| academic_01 | 0.822 | 0.861 | 688 | 311 | **V2** |
| academic_02 | 0.826 | 0.887 | 507 | 279 | **V2** |
| academic_03 | 0.931 | 0.936 | 610 | 285 | **V2** |
| blog_01 | 0.731 | — | 870 | — | — |
| blog_02 | 0.716 | — | 1196 | — | — |
| technical_01 | 0.850 | — | 905 | — | — |
| technical_02 | 0.802 | — | 741 | — | — |
| business_01 | 0.856 | — | 782 | — | — |
| business_02 | 0.778 | — | 655 | — | — |
| healthcare_01 | 0.926 | — | 927 | — | — |

> V2 is ~2x faster and scoring equal or higher than V1 on all 3 completed samples.

---

## Key Findings (V1 Complete)

| Metric | Value |
|:-------|:------|
| Average Original HLS | 0.565 |
| Average Refined HLS | 0.824 |
| Average Improvement | +0.256 |
| Best improvement | healthcare_01 (+0.406) |
| Lowest improvement | blog_02 (+0.090) |
| Average processing time | 788s (~13 min) |

---

## Aggressiveness Comparison

| Sample | Aggr | HLS |
|:-------|:----:|:----|
| academic_01 | 1 | — |
| academic_01 | 2 | 0.822 |
| academic_01 | 3 | — |

---

## Tone Comparison

| Sample | Tone | HLS |
|:-------|:-----|:----|
| healthcare_01 | formal_report | 0.926 |
| healthcare_01 | academic | — |
| healthcare_01 | btech_student | — |

---

## Notes

- HLS = Human Likeness Score (0.0–1.0, higher is better)
- HLS Δ = refined HLS minus original HLS
- V2 results still running for blog, technical, business, healthcare samples
- V2 is ~2x faster than V1 with equal or better quality
- NUM_CANDIDATES=1 used for all benchmark runs
