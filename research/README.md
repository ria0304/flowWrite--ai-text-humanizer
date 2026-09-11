# FlowWrite Research Framework

This directory contains the complete experimental framework for transforming FlowWrite from a software project into a research contribution.

## Quick Start

```bash
# 1. Generate dataset (already done)
python research/dataset_generator.py

# 2. Run enhanced metrics test
python research/evaluation/enhanced_metrics.py

# 3. Generate human evaluation forms (already done)
python research/human_eval/evaluation_form.py

# 4. Test baseline methods
python research/baselines/simple_paraphraser.py

# 5. Run full benchmark (requires pipeline integration)
python research/experiments/run_large_scale_benchmark.py
```

## What's Included

| Component | File | Status |
|-----------|------|--------|
| Dataset Generator | `dataset_generator.py` | ✅ Complete (144 docs) |
| Enhanced Metrics | `evaluation/enhanced_metrics.py` | ✅ Complete |
| Human Eval Forms | `human_eval/evaluation_form.py` | ✅ Ready to deploy |
| Baseline Methods | `baselines/simple_paraphraser.py` | ✅ Complete |
| Benchmark Runner | `experiments/run_large_scale_benchmark.py` | ⚠️ Needs pipeline connection |
| Paper Outline | `paper_outline.md` | ✅ Complete draft |
| Progress Tracker | `RESEARCH_PROGRESS.md` | ✅ Maintained |

## Generated Data

- **144 documents** across 6 domains × 4 LLM styles
- Location: `research/datasets/generated/`
- Includes individual text files + metadata JSON

## Research Questions

1. **RQ1 — Human-likeness:** Does FlowWrite produce text judged more human-like than original AI text?
2. **RQ2 — Semantic preservation:** Does FlowWrite preserve the meaning of the original text?
3. **RQ3 — Quality/speed trade-off:** Does removing the Flow Smoother reduce quality while significantly improving processing time?
4. **RQ4 — Robustness:** Does FlowWrite's performance remain consistent across different domains and LLM sources?

## Key Finding (Preliminary)

> **V2 removes an entire LLM pass, becomes ~3× faster, and slightly improves average HLS from 0.824 → 0.839.**
> 
> However, V1 performs better for Blog and Healthcare domains where flow smoothing adds value.

## Next Steps

1. **Integrate with actual FlowWrite pipeline** (modify benchmark runner)
2. **Execute full experiment** on all 144 documents
3. **Conduct human evaluation study** (forms ready)
4. **Perform statistical analysis**
5. **Write paper** using outline provided

## Timeline

Estimated **4-6 weeks** to submission-ready manuscript (see `RESEARCH_PROGRESS.md` for details)

## Citation (Future)

```bibtex
@article{flowwrite2025,
  title={FlowWrite: A Multi-Stage LLM-Based Text Rewriting Framework},
  author={},
  journal={},
  year={2025}
}
```

---

**For detailed progress tracking:** See `RESEARCH_PROGRESS.md`


**Last updated:** September 3, 2025
