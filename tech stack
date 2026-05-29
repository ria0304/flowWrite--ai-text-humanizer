# 🛠️ FlowWrite — Tech Stack

![Python](https://img.shields.io/badge/Python-3.11-blue?style=flat-square&logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?style=flat-square&logo=fastapi)
![Ollama](https://img.shields.io/badge/Ollama-llama3.2-black?style=flat-square)
![spaCy](https://img.shields.io/badge/spaCy-3.7.4-09A3D5?style=flat-square&logo=spacy)
![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│  🌐  FRONTEND  ·  index.html  ·  localhost:3000                 │
│                                                                 │
│   [Type / Paste]  [Upload File]  [Tone]  [Intensity]  [Scores] │
└────────────────────────┬────────────────────────────────────────┘
                         │  fetch() · JSON / FormData
┌────────────────────────▼────────────────────────────────────────┐
│  ⚡  FASTAPI BACKEND  ·  main.py  ·  localhost:8000             │
│                                                                 │
│   POST /rewrite   POST /rewrite-file                           │
│   POST /evaluate  POST /rewrite-and-evaluate                   │
└────────────────────────┬────────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────────┐
│  🔧  4-STAGE PIPELINE  ·  pipeline/  ·  shared_models.py        │
│                                                                 │
│   [Stage 1]      [Stage 2]      [Stage 3]      [Stage 4]       │
│   Chunker   →  Sem. Merge  →  Style Rewrite →  Flow Smooth     │
│   (spaCy)      (SBERT)        (Ollama LLM)     (Ollama LLM)    │
└────────────────────────┬────────────────────────────────────────┘
                         │  HTTP · httpx
┌────────────────────────▼────────────────────────────────────────┐
│  🤖  AI / MODELS  ·  Ollama  ·  localhost:11434                 │
│                                                                 │
│   llama3.2:latest (2 GB)       mistral:latest (4.4 GB)         │
│   SBERT all-MiniLM-L6-v2       spaCy en_core_web_sm            │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│  📊  EVALUATION  ·  evaluation/  ·  hls.py aggregates           │
│                                                                 │
│   Burstiness · Coherence · Readability · Connectors            │
│   Semantic Similarity · AI Phrase Detector                     │
└─────────────────────────────────────────────────────────────────┘
```

---

## Stack Summary

| Layer | Technology | Details |
|:------|:-----------|:--------|
| **Frontend** | HTML + CSS + JS | Single-page UI, no framework |
| **Frontend server** | `python -m http.server` | Serves `index.html` on port 3000 |
| **Backend** | FastAPI + Uvicorn | REST API on port 8000 |
| **NLP chunking** | spaCy 3.7.4 | Sentence segmentation via `en_core_web_sm` |
| **Embeddings** | SBERT `all-MiniLM-L6-v2` | Semantic similarity scoring |
| **LLM rewriting** | Ollama (llama3.2 / mistral) | Style rewrite + flow smoothing |
| **File parsing** | pdfplumber + python-docx | PDF and DOCX text extraction |
| **Evaluation** | 6 custom metrics | Human Likeness Score (HLS) |

---

## Pipeline Stages

| # | Stage | File | What it does |
|:--|:------|:-----|:-------------|
| 1 | **Chunker** | `pipeline/chunker.py` | Splits text into sentence groups using spaCy |
| 2 | **Semantic Merge** | `pipeline/semantic_merge.py` | Merges related chunks using SBERT embeddings |
| 3 | **Style Rewriter** | `pipeline/style_rewriter.py` | Rewrites each unit via Ollama with tone + intensity |
| 4 | **Flow Smoother** | `pipeline/flow_smoother.py` | Final LLM pass — removes AI patterns, varies rhythm |

---

## Evaluation Metrics

| Metric | File | Weight in HLS | What it measures |
|:-------|:-----|:-------------:|:----------------|
| **Burstiness** | `evaluation/burstiness.py` | 20% | Sentence length variation |
| **Coherence** | `evaluation/coherence.py` | 30% | Logical flow between sentences |
| **Readability** | `evaluation/readability.py` | 20% | Flesch reading ease score |
| **Connector density** | `evaluation/connector_density.py` | 15% | Natural transition word usage |
| **Semantic similarity** | `evaluation/semantic_similarity.py` | 10% | Meaning preserved vs original |
| **AI phrase score** | `evaluation/ai_phrase_detector.py` | 5% | Detects and penalises AI phrases |

---

