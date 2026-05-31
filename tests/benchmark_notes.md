# FlowWrite — Benchmark Results

## Test Configuration

| Setting | Value |
|:--------|:------|
| Model | llama3.2:latest |
| NUM_CANDIDATES | 1 (benchmarking) / 3 (production) |
| Pipeline version | v1.0 |
| Date tested | 31 May 2026 |

---

## Results

| Sample | Tone | Aggr | Original HLS | Refined HLS | HLS Δ | Time (s) |
|:-------|:-----|:----:|:------------:|:-----------:|:-----:|:--------:|
| academic_01 | academic | 2 | 0.563 | 0.822 | +0.259 | 688 |
| academic_02 | academic | 2 | 0.653 | 0.826 | +0.173 | 507 |
| academic_03 | academic | 2 | 0.572 | 0.931 | +0.358 | 610 |
| blog_01 | conversational | 2 | 0.624 | 0.812 | +0.188 | — |
| blog_02 | conversational | 2 | 0.626 | 0.831 | +0.205 | — |
| technical_01 | technical | 2 | — | — | — | — |
| technical_02 | technical | 2 | — | — | — | — |
| business_01 | formal_professional | 2 | — | — | — | — |
| business_02 | formal_professional | 2 | — | — | — | — |
| healthcare_01 | formal_report | 2 | — | — | — | — |

---

## V1 vs V2 Pipeline Comparison

| Sample | V1 HLS | V2 HLS | V1 Time (s) | V2 Time (s) | Winner |
|:-------|:------:|:------:|:-----------:|:-----------:|:------:|
| academic_01 | 0.822 | — | 688 | — | — |
| academic_02 | 0.826 | — | 507 | — | — |
| academic_03 | 0.931 | — | 610 | — | — |
| blog_01 | 0.812 | — | — | — | — |
| blog_02 | 0.831 | — | — | — | — |
| technical_01 | — | — | — | — | — |
| technical_02 | — | — | — | — | — |
| business_01 | — | — | — | — | — |
| business_02 | — | — | — | — | — |
| healthcare_01 | — | — | — | — | — |

---

## Key Findings So Far

| Metric | Value |
|:-------|:------|
| Average Original HLS | 0.608 |
| Average Refined HLS | 0.844 |
| Average Improvement | +0.237 |
| Best improvement | academic_03 (+0.358) |
| Lowest improvement | academic_02 (+0.173) |

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
| healthcare_01 | formal_report | — |
| healthcare_01 | academic | — |
| healthcare_01 | btech_student | — |

---

## Notes

- HLS = Human Likeness Score (0.0–1.0, higher is better)
- HLS Δ = refined HLS minus original HLS
- blog_01 and blog_02 times are from old NUM_CANDIDATES=3 run
- academic samples are from new NUM_CANDIDATES=1 run (~10 min each)
- Update this file as more results come in
