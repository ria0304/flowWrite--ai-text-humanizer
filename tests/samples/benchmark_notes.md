# FlowWrite — Benchmark Results

## Test Configuration

| Setting | Value |
|:--------|:------|
| Model | llama3.2:latest |
| NUM_CANDIDATES | 3 |
| Pipeline version | v1.0 |
| Date tested | — |

---

## Results

| Sample | Tone | Aggr | Original HLS | Refined HLS | HLS Δ | GPTZero | ZeroGPT | QuillBot | Turnitin |
|:-------|:-----|:----:|:------------:|:-----------:|:-----:|:-------:|:-------:|:--------:|:--------:|
| academic_01 | academic | 2 | — | — | — | — | — | — | — |
| academic_02 | academic | 2 | — | — | — | — | — | — | — |
| academic_03 | academic | 2 | — | — | — | — | — | — | — |
| blog_01 | conversational | 2 | — | — | — | — | — | — | — |
| blog_02 | conversational | 2 | — | — | — | — | — | — | — |
| technical_01 | technical | 2 | — | — | — | — | — | — | — |
| technical_02 | technical | 2 | — | — | — | — | — | — | — |
| business_01 | formal_professional | 2 | — | — | — | — | — | — | — |
| business_02 | formal_professional | 2 | — | — | — | — | — | — | — |
| healthcare_01 | formal_report | 2 | — | — | — | — | — | — | — |

---

## How to run

```bash
# Single sample
curl -X POST http://localhost:8000/rewrite-and-evaluate \
  -H "Content-Type: application/json" \
  -d '{
    "text": "'$(cat tests/samples/academic_01.txt)'",
    "tone": "academic",
    "aggressiveness": 2
  }'

# Or use the /rewrite-file endpoint
curl -X POST http://localhost:8000/rewrite-file \
  -F "file=@tests/samples/academic_01.txt" \
  -F "tone=academic" \
  -F "aggressiveness=2"
```

---

## Aggressiveness Comparison

Test `academic_01` across all aggressiveness levels to see the impact:

| Sample | Aggr | HLS | GPTZero | ZeroGPT |
|:-------|:----:|:----|:--------|:--------|
| academic_01 | 1 | — | — | — |
| academic_01 | 2 | — | — | — |
| academic_01 | 3 | — | — | — |

---

## Tone Comparison

Test `healthcare_01` across multiple tones:

| Sample | Tone | HLS | GPTZero | ZeroGPT |
|:-------|:-----|:----|:--------|:--------|
| healthcare_01 | formal_report | — | — | — |
| healthcare_01 | academic | — | — | — |
| healthcare_01 | btech_student | — | — | — |

---

## Notes

- HLS = Human Likeness Score (0–100)
- HLS Δ = refined HLS minus original HLS
- All detector scores = % human (higher is better)
- Add rows as more samples are tested
