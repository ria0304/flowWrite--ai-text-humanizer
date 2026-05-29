# FlowWrite — Discourse Rewriter

A multi-pass NLP pipeline that rewrites AI-generated text into natural, 
connected, human-like academic writing.

## Pipeline Stages
1. **Chunk** — spaCy splits text into sentence groups
2. **Semantic Merge** — SBERT embeddings merge related sentences
3. **Style Rewrite** — Local LLM rewrites with tone + aggressiveness
4. **Flow Smooth** — Final LLM pass for transitions and variety

---

## Setup

### 1. Install Ollama (Local LLM)
```bash
# Download from https://ollama.com
# Then pull a model:
ollama pull mistral
# or
ollama pull llama3
```

### 2. Backend Setup
```bash
cd backend
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

### 3. Run Backend
```bash
cd backend
uvicorn main:app --reload --port 8000
```

### 4. Open Frontend
Just open `frontend/index.html` in your browser.
(No server needed for frontend)

---

## Change LLM Model
In `backend/pipeline/style_rewriter.py` and `flow_smoother.py`:
```python
MODEL_NAME = "mistral"   # change to: llama3, gemma, phi3, etc.
```

## Tune Similarity Threshold
In `backend/pipeline/semantic_merge.py`:
```python
SIMILARITY_THRESHOLD = 0.55  # higher = less merging, lower = more merging
```

---

## Project Structure
```
humanizer/
├── backend/
│   ├── main.py                  # FastAPI app
│   ├── requirements.txt
│   └── pipeline/
│       ├── chunker.py           # Stage 1
│       ├── semantic_merge.py    # Stage 2
│       ├── style_rewriter.py    # Stage 3
│       └── flow_smoother.py     # Stage 4
│       └── pipeline_controller.py
└── frontend/
    └── index.html               # Full UI
```
