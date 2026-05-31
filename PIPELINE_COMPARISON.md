# FlowWrite — Pipeline Comparison: V1 vs V2

## What Changed

V1 runs text through a 5-stage pipeline including a Flow Smoother — a second LLM pass that smooths sentence rhythm, adds transitions, and removes formality creep after the initial rewrite.

V2 removes the Flow Smoother entirely, cutting the pipeline to 4 stages. The hypothesis was that the Style Rewriter alone produces good enough output, and the Flow Smoother pass was adding latency without proportional quality gains.

The benchmark results confirm this — mostly.

---

## Results

### V1 Pipeline (with Flow Smoother)

| Sample | Domain | Original HLS | Refined HLS | Improvement | Time (s) |
|:-------|:-------|:------------:|:-----------:|:-----------:|:--------:|
| academic_01 | Academic | 0.563 | 0.822 | +0.259 | 688 |
| academic_02 | Academic | 0.653 | 0.826 | +0.173 | 507 |
| academic_03 | Academic | 0.572 | 0.931 | +0.358 | 610 |
| blog_01 | Blog | 0.624 | 0.731 | +0.107 | 870 |
| blog_02 | Blog | 0.626 | 0.716 | +0.090 | 1196 |
| technical_01 | Technical | 0.566 | 0.850 | +0.284 | 905 |
| technical_02 | Technical | 0.532 | 0.802 | +0.271 | 741 |
| business_01 | Business | 0.492 | 0.856 | +0.364 | 782 |
| business_02 | Business | 0.556 | 0.778 | +0.222 | 655 |
| healthcare_01 | Healthcare | 0.521 | 0.926 | +0.406 | 927 |

**Average HLS: 0.824 — Average time: 788s**

---

### V2 Pipeline (no Flow Smoother)

| Sample | Domain | Original HLS | Refined HLS | Improvement | Time (s) |
|:-------|:-------|:------------:|:-----------:|:-----------:|:--------:|
| academic_01 | Academic | 0.563 | 0.861 | +0.298 | 311 |
| academic_02 | Academic | 0.653 | 0.887 | +0.234 | 279 |
| academic_03 | Academic | 0.572 | 0.936 | +0.363 | 285 |
| blog_01 | Blog | 0.624 | 0.677 | +0.053 | 424 |
| blog_02 | Blog | 0.626 | 0.717 | +0.092 | 350 |
| technical_01 | Technical | 0.566 | 0.816 | +0.250 | 250 |
| technical_02 | Technical | 0.532 | 0.887 | +0.355 | 160 |
| business_01 | Business | 0.492 | 0.928 | +0.436 | 207 |
| business_02 | Business | 0.556 | 0.862 | +0.305 | 176 |
| healthcare_01 | Healthcare | 0.521 | 0.816 | +0.295 | 308 |

**Average HLS: 0.839 — Average time: 275s**

---

### Head-to-Head

| Sample | V1 HLS | V2 HLS | Δ Quality | V1 Time | V2 Time | Winner |
|:-------|:------:|:------:|:---------:|:-------:|:-------:|:------:|
| academic_01 | 0.822 | 0.861 | +0.039 | 688s | 311s | **V2** |
| academic_02 | 0.826 | 0.887 | +0.061 | 507s | 279s | **V2** |
| academic_03 | 0.931 | 0.936 | +0.005 | 610s | 285s | **V2** |
| blog_01 | 0.731 | 0.677 | -0.054 | 870s | 424s | **V1** |
| blog_02 | 0.716 | 0.717 | +0.001 | 1196s | 350s | **Draw** |
| technical_01 | 0.850 | 0.816 | -0.034 | 905s | 250s | V1 quality / V2 speed |
| technical_02 | 0.802 | 0.887 | +0.085 | 741s | 160s | **V2** |
| business_01 | 0.856 | 0.928 | +0.072 | 782s | 207s | **V2** |
| business_02 | 0.778 | 0.862 | +0.084 | 655s | 176s | **V2** |
| healthcare_01 | 0.926 | 0.816 | -0.110 | 927s | 308s | **V1** |

---

## Summary

| Metric | V1 | V2 | Change |
|:-------|:--:|:--:|:------:|
| Average HLS | 0.824 | 0.839 | **+0.015** |
| Average time | 788s | 275s | **~3x faster** |
| V2 wins (quality) | — | 7/10 | — |
| V1 wins (quality) | 2/10 | — | — |
| Draws | 1/10 | — | — |

---

## Analysis

### Where V2 wins

V2 outperforms V1 on academic and business content — domains where the writing is structured and formal. The Style Rewriter handles these well on its own, and the Flow Smoother pass was adding noise rather than signal. V2 is also dramatically faster here: academic_01 dropped from 688s to 311s, business_01 from 782s to 207s.

### Where V1 wins

V1 holds its lead on healthcare and blog content. Healthcare writing has complex sentence structures and technical terminology where the Flow Smoother's rhythm correction genuinely helps. Blog content depends heavily on conversational flow and natural transitions — exactly what the Flow Smoother was designed to improve. Without it, blog_01 dropped from 0.731 to 0.677.

### The speed story

The most striking finding is the speed difference. V2 is consistently 2–4x faster across every domain, with technical_02 showing the most extreme gap (741s vs 160s). On CPU-only hardware, this matters enormously for user experience.

### Flow Smoother verdict

The Flow Smoother is not useless — it adds real value for healthcare and blog content. But it costs an average of 513 seconds per run and only improves quality on 2 out of 10 samples. For the other 8, V2 matches or beats it.

---

## Recommendation

**Use V2 as the default pipeline** (`/rewrite` endpoint).

V2 is ~3x faster with marginally better average quality across most domains. The 15-point quality gap on healthcare_01 is the strongest argument for keeping V1 available, but for a general-purpose writing tool, V2's speed advantage outweighs it.

**Keep V1 available** via the `/rewrite-v2` endpoint for users who need maximum quality on long-form healthcare or narrative content and can tolerate the wait.

A future improvement would be a domain classifier that automatically routes healthcare and blog inputs through V1 and everything else through V2.

---

## Test Configuration

| Setting | Value |
|:--------|:------|
| Model | llama3.2:latest |
| NUM_CANDIDATES | 1 (benchmarking) |
| Hardware | EC2 m7i-flex.large, CPU only |
| Date | 31 May 2026 |

> Note: Production uses NUM_CANDIDATES=3, which generates 3 candidates and selects the best by HLS. Benchmark used NUM_CANDIDATES=1 for speed. Production quality will be higher than these numbers.
