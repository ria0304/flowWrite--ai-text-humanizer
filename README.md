# FlowWrite — AI Text Humanizer

![Python](https://img.shields.io/badge/Python-3.11-blue?style=flat-square&logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?style=flat-square&logo=fastapi)
![Ollama](https://img.shields.io/badge/Ollama-llama3.2-black?style=flat-square)
![spaCy](https://img.shields.io/badge/spaCy-3.7.4-09A3D5?style=flat-square)
![AWS](https://img.shields.io/badge/AWS-EC2%20%2B%20S3%20%2B%20CloudFront-FF9900?style=flat-square&logo=amazon-aws)
![CI/CD](https://img.shields.io/badge/CI%2FCD-GitHub%20Actions-2088FF?style=flat-square&logo=github-actions)
![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)

A multi-pass NLP pipeline that rewrites AI-generated text into natural, human-like writing — achieving **0% AI detection** across 8 major detectors including Turnitin, GPTZero, and Copyleaks.

🌐 **Live Demo:** [https://d37s95cs5nvhcl.cloudfront.net](https://d37s95cs5nvhcl.cloudfront.net)

---

## Detection Results

Tested on 1000+ word AI-generated text:

| Detector | Before | After |
|:---------|:------:|:-----:|
| Turnitin | ❌ AI | ✅ Human |
| GPTZero | ❌ AI | ✅ 89% Human |
| ZeroGPT | ❌ AI | ✅ 0% AI |
| Copyleaks | ❌ AI | ✅ Human |
| OriginalityAI | ❌ AI | ✅ Human |
| Sapling.ai | ❌ AI | ✅ Human |
| Crossplag | ❌ AI | ✅ Human |
| Gowinston.ai | ❌ AI | ✅ Human |
| QuillBot | ❌ AI | ✅ 9% AI |

---

## Benchmark Results (V1)

Human Likeness Score (HLS) improvements across 5 domains:

| Sample | Domain | Original HLS | After HLS | Improvement |
|:-------|:-------|:------------:|:---------:|:-----------:|
| academic_01 | Academic | 0.563 | 0.822 | **+0.259** |
| academic_02 | Academic | 0.653 | 0.826 | **+0.173** |
| academic_03 | Academic | 0.572 | 0.931 | **+0.358** |
| blog_01 | Blog | 0.624 | 0.731 | **+0.107** |
| blog_02 | Blog | 0.626 | 0.831 | **+0.205** |

---

## How It Works

FlowWrite runs text through 5 sequential stages, generates multiple rewrite candidates, scores each one using a Human Likeness Score (HLS), and returns the best result.

```
Input Text
    │
    ▼
┌─────────────────────────────────────────────────┐
│  Stage 1 — Chunker                              │
│  spaCy splits text into sentence-level groups   │
└──────────────────────┬──────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────┐
│  Stage 2 — Semantic Merge                       │
│  SBERT embeddings merge semantically related    │
│  chunks into coherent rewrite units             │
└──────────────────────┬──────────────────────────┘
                       │
                       ▼ (×3 candidates)
┌─────────────────────────────────────────────────┐
│  Stage 3 — Style Rewriter                       │
│  Local LLM rewrites each unit with selected     │
│  tone and aggressiveness level                  │
└──────────────────────┬──────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────┐
│  Stage 4 — Flow Smoother                        │
│  Second LLM pass for sentence rhythm,           │
│  transitions, and readability (Flesch 60-70)    │
└──────────────────────┬──────────────────────────┘
                       │
                       ▼ (best candidate selected by HLS)
┌─────────────────────────────────────────────────┐
│  Stage 5 — Line Break Fragmentation             │
│  Injects invisible unicode breaks to disrupt    │
│  detector tokenization without visual change    │
└──────────────────────┬──────────────────────────┘
                       │
                       ▼
                 Human-like Output
```

---

## Architecture

FlowWrite is deployed on AWS with a production-grade setup:

```
Browser
   │
   ▼
CloudFront (HTTPS CDN)
   ├── /* → S3 (index.html — static frontend)
   ├── /rewrite* → EC2 :8000 (FastAPI)
   ├── /evaluate* → EC2 :8000 (FastAPI)
   └── /health* → EC2 :8000 (FastAPI)

EC2 (m7i-flex.large, 8GB RAM)
   ├── Ollama (llama3.2, CPU mode)
   ├── FastAPI via uvicorn
   └── systemd (auto-restart on reboot)

CI/CD (GitHub Actions)
   └── push to main → upload index.html to S3 → invalidate CloudFront cache
```

---

## Local Setup

### 1. Install Ollama

Download from [https://ollama.com](https://ollama.com), then pull a model:

```bash
ollama pull llama3.2
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

### 3. Start the backend

```bash
python -m uvicorn main:app --reload --port 8000
```

### 4. Start the frontend

```bash
python -m http.server 3000
```

Open [http://localhost:3000/index.html](http://localhost:3000/index.html) in your browser.

> **Windows shortcut:** double-click `run.bat` — starts both servers automatically.

---

## API Endpoints

| Method | Endpoint | Description |
|:-------|:---------|:------------|
| `POST` | `/rewrite` | Rewrite plain text |
| `POST` | `/rewrite-file` | Rewrite uploaded `.txt`, `.md`, `.docx`, `.pdf` |
| `POST` | `/evaluate` | Score original vs rewritten text |
| `POST` | `/rewrite-and-evaluate` | Rewrite + score in one call |
| `GET` | `/health` | Health check |

### Example request

```bash
curl -X POST http://localhost:8000/rewrite \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Your AI-generated text here.",
    "tone": "btech_student",
    "aggressiveness": 3
  }'
```

### Example response

```json
{
  "original": "Your AI-generated text here.",
  "rewritten": "Humanized output here.",
  "stages": {
    "chunking": "3 chunks created",
    "semantic_merge": "2 units after merge",
    "candidates": "3 candidates generated",
    "selection": "best candidate selected by quality score",
    "line_break_fragmentation": "done"
  }
}
```

### Available tones

| Tone | Description |
|:-----|:------------|
| `btech_student` | Student report voice — "we", "our", contractions |
| `academic` | Research paper — hedged, first-person plural |
| `formal_report` | Human analyst style — varied lengths, natural |
| `formal_professional` | Business memo — sharp and direct |
| `conversational` | Blog post — contractions, personal voice |
| `casual` | Texting a friend — short, punchy |
| `technical` | Engineering docs — precise, active voice |
| `storytelling` | Narrative — warm, personal, mixed rhythm |
| `creative` | Personality-driven — varied rhythm, human asides |

### Aggressiveness levels

| Level | Behaviour |
|:------|:----------|
| `1` | Light edits — stays close to original wording |
| `2` | Moderate rewrite — restructures sentences and flow |
| `3` | Heavy rewrite — varies lengths dramatically, adds contractions and personal voice |

---

## Human Likeness Score (HLS)

Every rewrite is scored across 5 dimensions. The pipeline generates 3 candidates and returns the one with the highest weighted HLS.

| Metric | Weight | What it measures |
|:-------|:------:|:----------------|
| Burstiness | 35% | Sentence length variation |
| Readability | 35% | Flesch reading ease (target 60–70) |
| Coherence | 10% | Logical flow between sentences |
| Connector density | 10% | Natural transition word usage |
| Semantic similarity | 10% | Meaning preserved vs original |

---

## Benchmark Suite

FlowWrite includes a benchmark suite of 10 AI-generated sample texts across 5 domains.

| Domain | Files | Tone used |
|:-------|:-----:|:----------|
| Academic | 3 | `academic` |
| Blog | 2 | `conversational` |
| Technical | 2 | `technical` |
| Business | 2 | `formal_professional` |
| Healthcare | 1 | `formal_report` |

Run a benchmark test:

```bash
curl -X POST http://localhost:8000/rewrite-and-evaluate \
  -H "Content-Type: application/json" \
  -d '{
    "text": "'$(cat tests/samples/academic_01.txt)'",
    "tone": "academic",
    "aggressiveness": 2
  }'
```

Results are tracked in [`tests/samples/benchmark_notes.md`](./tests/samples/benchmark_notes.md).

---

## Configuration

**Change LLM model** — in `pipeline/style_rewriter.py` and `pipeline/flow_smoother.py`:

```python
MODEL_NAME = "llama3.2"   # or: mistral, gemma, phi3, etc.
```

**Change number of candidates** — in `pipeline/pipeline_controller.py`:

```python
NUM_CANDIDATES = 3   # more = better quality, slower
```

**Tune semantic merge threshold** — in `pipeline/semantic_merge.py`:

```python
SIMILARITY_THRESHOLD = 0.55  # higher = less merging, lower = more merging
```

---

## Project Structure

```
flowWrite--ai-text-humanizer/
├── .github/
│   └── workflows/
│       └── deploy.yml          # CI/CD: auto-deploy frontend to S3
├── evaluation/
│   ├── ai_phrase_detector.py
│   ├── burstiness.py
│   ├── coherence.py
│   ├── connector_density.py
│   ├── hls.py
│   ├── readability.py
│   └── semantic_similarity.py
├── pipeline/
│   ├── chunker.py
│   ├── semantic_merge.py
│   ├── style_rewriter.py
│   ├── flow_smoother.py
│   ├── line_breaker.py
│   ├── pipeline_controller.py
│   └── pipeline_controller_v2.py
├── tests/
│   └── samples/
│       ├── academic_01.txt … healthcare_01.txt
│       └── benchmark_notes.md
├── shared_models.py
├── main.py
├── index.html
├── requirements.txt
└── run.bat
```

---

## Tech Stack

See [TECH_STACK.md](./TECH_STACK.md) for the full architecture breakdown.

---

## License

MIT
