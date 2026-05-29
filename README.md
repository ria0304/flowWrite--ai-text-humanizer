# FlowWrite — AI Text Humanizer

![Python](https://img.shields.io/badge/Python-3.11-blue?style=flat-square&logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?style=flat-square&logo=fastapi)
![Ollama](https://img.shields.io/badge/Ollama-llama3.2-black?style=flat-square)
![spaCy](https://img.shields.io/badge/spaCy-3.7.4-09A3D5?style=flat-square)
![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)

A multi-pass NLP pipeline that rewrites AI-generated text into natural, human-like writing — with tone control, rewrite intensity, and a Human Likeness Score (HLS) evaluation system.

---

## Pipeline Stages

| # | Stage | What it does |
|:--|:------|:-------------|
| 1 | **Chunk** | spaCy splits text into sentence groups |
| 2 | **Semantic Merge** | SBERT embeddings merge related sentences |
| 3 | **Style Rewrite** | Local LLM rewrites with tone + aggressiveness |
| 4 | **Flow Smooth** | Final LLM pass for transitions and rhythm |

---

## Setup

### 1. Install Ollama

Download from [https://ollama.com](https://ollama.com), then pull a model:

```bash
ollama pull llama3.2
# or
ollama pull mistral
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

Then open [http://localhost:3000/index.html](http://localhost:3000/index.html) in your browser.

> **Windows shortcut:** just double-click `run.bat` — it starts both servers automatically.

---

## Configuration

**Change LLM model** — in `pipeline/style_rewriter.py` and `pipeline/flow_smoother.py`:

```python
MODEL_NAME = "llama3.2"   # or: mistral, gemma, phi3, etc.
```

**Tune similarity threshold** — in `pipeline/semantic_merge.py`:

```python
SIMILARITY_THRESHOLD = 0.55  # higher = less merging, lower = more merging
```

---

## Evaluation Metrics

FlowWrite scores every rewrite across 6 metrics and combines them into a **Human Likeness Score (HLS)**:

| Metric | Weight | What it measures |
|:-------|:------:|:----------------|
| Coherence | 30% | Logical flow between sentences |
| Burstiness | 20% | Sentence length variation |
| Readability | 20% | Flesch reading ease |
| Connector density | 15% | Natural transition word usage |
| Semantic similarity | 10% | Meaning preserved vs original |
| AI phrase score | 5% | Penalises AI-sounding phrases |

---

## API Endpoints

| Method | Endpoint | Description |
|:-------|:---------|:------------|
| `POST` | `/rewrite` | Rewrite plain text |
| `POST` | `/rewrite-file` | Rewrite uploaded `.txt`, `.md`, `.docx`, `.pdf` |
| `POST` | `/evaluate` | Score original vs rewritten text |
| `POST` | `/rewrite-and-evaluate` | Rewrite + score in one call |
| `GET` | `/health` | Health check |

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
