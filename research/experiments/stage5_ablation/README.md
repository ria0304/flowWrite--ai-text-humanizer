# Stage 5 Ablation Experiment

## Research Objective

This experiment isolates the effect of **Stage 5 (Line Break Fragmentation)** on:
1. Detector robustness (when external detectors are integrated)
2. Content preservation
3. Visual/rendering preservation
4. Unicode representation changes

**Research Question:** Does Stage 5 (Unicode line-break fragmentation) improve detector robustness while preserving the original content and visual appearance?

## Experimental Design

### Control vs Treatment

| Condition | Stages 1-4 | Stage 5 | Description |
|-----------|------------|---------|-------------|
| **Control** | ✅ Executed | ❌ Skipped | Pipeline output before Stage 5 perturbation |
| **Treatment** | ✅ Executed | ✅ Applied | Full pipeline with Stage 5 Unicode insertion |

**Key:** The ONLY difference between conditions is `enable_stage5` parameter.

### Pipeline Configuration

- **Pipeline Version:** V2 (no flow smoother) - chosen for efficiency
- **Tone:** formal_report
- **Aggressiveness:** 2 (medium)
- **Max Words:** 5000

### Dataset

- **Source:** `research/datasets/generated/`
- **Type:** Template-simulated LLM styles (clearly labeled as simulated)
- **Domains:** Academic, Technical, Business, Blog, Healthcare, General
- **Pilot Size:** 20 documents
- **Full Experiment Size:** 100+ documents

## How to Run

### Prerequisites

1. Ollama server running with required models
2. Python 3.12+ environment
3. Dependencies installed (`pip install -r requirements.txt`)

### Execute Experiment

```bash
cd /workspace
python research/experiments/stage5_ablation/run_experiment.py --pilot
```

For full experiment (100+ documents):

```bash
python research/experiments/stage5_ablation/run_experiment.py --full
```

### Analyze Results

```bash
python research/experiments/stage5_ablation/analyze_results.py
```

## Output Structure

```
results/
├── raw/                    # Individual document results (JSON)
│   ├── {doc_id}_control.json
│   └── {doc_id}_treatment.json
├── processed/              # Aggregated data (CSV/JSON)
│   ├── experiment_results.csv
│   └── stage5_metadata.json
├── tables/                 # Statistical tables (LaTeX/Markdown)
│   └── main_results.tex
└── figures/                # Visualization plots
    ├── perturbation_distribution.png
    └── survival_rates.png
```

## Recorded Metadata

Each experimental result includes:

- `experiment_id`: Unique identifier
- `document_id`: Source document identifier
- `dataset_version`: Dataset version tag
- `condition`: "control" or "treatment"
- `stage5_enabled`: Boolean
- `python_version`: Python interpreter version
- `package_versions`: Key package versions
- `model_name`: LLM model used
- `random_seed`: Seed for reproducibility
- `timestamp`: ISO format timestamp
- `input_length`: Character count before pipeline
- `intermediate_length`: Character count after Stage 4
- `final_output_length`: Character count after Stage 5 (if applied)
- `pipeline_success`: Boolean
- `failure_reason`: Error message if failed
- `stage5_metadata`: Perturbation counts and positions
- `evaluation_metrics`: HLS, semantic similarity, etc.

## Reproducibility

- All random operations seeded with value from `research/config/seeds.json`
- Python version recorded
- Package versions recorded via `pip freeze`
- Timestamp recorded for all operations
- Raw results preserved (never modified)

## Known Limitations

1. **Dataset:** Current dataset uses template-simulated LLM styles, not actual LLM outputs. Results should be interpreted accordingly.

2. **Detector Evaluation:** External detector integration not yet implemented. Current experiment measures internal metrics only.

3. **Visual Verification:** Rendering comparison not yet automated. Manual verification recommended.

4. **Normalization:** Unicode normalization effects measured but not controlled in downstream systems.

## Stage 5 Algorithm

Stage 5 inserts invisible Unicode characters:

- **ZWSP** (`\u200b`, ZERO-WIDTH SPACE): Before connector words, after clause patterns, before noun phrases, after semicolons
- **SHY** (`\u00ad`, SOFT HYPHEN): After comma-containing words

These characters are:
- Invisible in most renderers
- Intended to affect tokenizer behavior
- Measured for survival under NFC/NFD/NFKC/NFKD normalization

## Statistical Analysis

The analysis script performs:

1. Paired comparison (same document, control vs treatment)
2. Normality testing (Shapiro-Wilk)
3. Appropriate test selection (t-test or Mann-Whitney U)
4. Effect size calculation (Cohen's d)
5. Confidence intervals (95%)
6. Multiple comparison correction (Bonferroni)

## Citation

If using this experiment, cite:

```
FlowWrite: A Multi-Stage Text Rewriting Framework for Studying 
Unicode Perturbation Effects on AI-Text Detection
```

## License

See main repository LICENSE file.
