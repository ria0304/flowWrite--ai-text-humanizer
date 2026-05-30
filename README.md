# FlowWrite — AI Text Humanizer

![Python](https://img.shields.io/badge/Python-3.11-blue?style=flat-square&logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?style=flat-square&logo=fastapi)
![Ollama](https://img.shields.io/badge/Ollama-llama3.2-black?style=flat-square)
![spaCy](https://img.shields.io/badge/spaCy-3.7.4-09A3D5?style=flat-square)
![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)

A multi-pass NLP pipeline that rewrites AI-generated text into natural, human-like writing — achieving **0% AI detection** across Turnitin, GPTZero, ZeroGPT, Copyleaks, OriginalityAI, Sapling, Crossplag, and Gowinston.

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

## Detection Results

Tested on 1000+ word AI-generated text:

| Detector | Before | After |
|:---------|:------:|:-----:|
| Turnitin | ❌ AI | ✅ Human |
| GPTZero | ❌ AI | ✅ Human |
| ZeroGPT | ❌ AI | ✅ Human |
| Copyleaks | ❌ AI | ✅ Human |
| OriginalityAI | ❌ AI | ✅ Human |
| Sapling.ai | ❌ AI | ✅ Human |
| Crossplag | ❌ AI | ✅ Human |
| Gowinston.ai | ❌ AI | ✅ Human |

---

## Setup

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

Every rewrite is scored across 6 dimensions. The pipeline generates 3 candidates and returns the one with the highest weighted HLS.

| Metric | Weight | What it measures |
|:-------|:------:|:----------------|
| Burstiness | 35% | Sentence length variation |
| Readability | 35% | Flesch reading ease (target 60–70) |
| Coherence | 10% | Logical flow between sentences |
| Connector density | 10% | Natural transition word usage |
| Semantic similarity | 10% | Meaning preserved vs original |

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
humanizer_fixed/
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
│   └── pipeline_controller.py
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
