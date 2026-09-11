# FlowWrite — AI Text Humanizer

![Python](https://img.shields.io/badge/Python-3.11-blue?style=flat-square&logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?style=flat-square&logo=fastapi)
![Ollama](https://img.shields.io/badge/Ollama-llama3.2-black?style=flat-square)
![spaCy](https://img.shields.io/badge/spaCy-3.7.4-09A3D5?style=flat-square)
![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)

A multi-pass NLP pipeline that rewrites AI-generated text into natural, human-like writing — targeting low AI-detection scores across detectors including Turnitin, GPTZero, and Copyleaks.

> **Runs entirely locally.** Open `index.html` in a browser (or serve it with `python -m http.server`) and start the backend with `uvicorn main:app --port 8000`. No text leaves your machine.

---

## Two pipelines, and which endpoint actually runs which

FlowWrite ships two pipeline versions. **Their behavior does not match their endpoint names** — this trips people up, so read it once:

| Endpoint | Runs | Stages | Speed |
|:---------|:-----|:------:|:-----:|
| `/rewrite` | **V1** (`pipeline_controller.py`) | 5 — includes the Flow Smoother pass | Slower |
| `/rewrite-v2` | **V2** (`pipeline_controller_v2.py`) | 4 — no Flow Smoother | ~3x faster |

Benchmarking (see [`PIPELINE_COMPARISON.md`](./PIPELINE_COMPARISON.md)) found V2 matches or beats V1 on quality in 7 of 10 domain samples, and loses noticeably on healthcare and blog content, where the Flow Smoother's rhythm pass earns its keep. If you want the faster, generally-as-good pipeline, call `/rewrite-v2`, not `/rewrite`.

---

## Detection Results

Tested on 1000+ word AI-generated text, mainly against [humanizeai.pro/detector](https://www.humanizeai.pro/detector). These are results from the project's own testing, not an independent audit — treat them as directional.

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

## Benchmark Results

Human Likeness Score (HLS) improvements across 5 domains, 10 sample texts. Full numbers, per-sample timing, and the V1-vs-V2 breakdown are in [`PIPELINE_COMPARISON.md`](./PIPELINE_COMPARISON.md).

| Pipeline | Avg HLS | Avg time/run |
|:---------|:-------:|:------------:|
| V1 (`/rewrite`) | 0.824 | 788s |
| V2 (`/rewrite-v2`) | 0.839 | 275s |

---

## How It Works (V1 — `/rewrite`)

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

`/rewrite-v2` runs the same pipeline **minus Stage 4** — Style Rewriter output goes straight to line-break fragmentation.

---

## Architecture

```
Your Machine
   ├── Browser (index.html, opened directly or via a local static server)
   ├── FastAPI (localhost:8000)
   ├── Ollama (llama3.2, CPU)
   └── spaCy / SBERT
```

The frontend talks directly to `http://localhost:8000`. There is no cloud component and no telemetry — everything happens on the machine you run it on.

---

## Setup

### 1. Install Ollama

Download from [https://ollama.com](https://ollama.com), then pull the model:

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
python -m uvicorn main:app --port 8000
```

You should see:

```
INFO:     Started server process [xxxxx]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
```

Keep this terminal open — closing it shuts down the backend.

### 4. Open the app

Open `index.html` directly in your browser, or serve it locally to avoid `file://` restrictions:

```bash
python -m http.server 5500
```

Then visit `http://localhost:5500`. The API URL field in the top of the page defaults to `http://localhost:8000` and is editable if your backend runs elsewhere.

### Windows shortcut

`run.bat` automates all of the above in one step: it activates a virtual environment named `humanizer_env` (create this first with `python -m venv humanizer_env` and install requirements into it), starts the backend on port **8000**, starts a static file server on port **3000**, and opens `http://localhost:3000/index.html` in your browser automatically. It is not simply a shortcut for the `uvicorn` command — it manages both servers and the browser launch.

There is no equivalent `run.sh` for macOS/Linux in this repo. On those platforms, start Ollama and the backend manually as shown below.

---

## Running the Backend

```bash
# Terminal 1 — Ollama must be running before the backend
ollama serve

# Terminal 2 — FastAPI backend
python -m uvicorn main:app --port 8000 --reload
```

### Verify the backend is running

```
http://localhost:8000/health
```

Expected response:

```json
{ "status": "ok", "ollama": "ok", "ollama_model": "llama3.2:latest" }
```

If Ollama isn't reachable, `ollama` will report `"unreachable"` here even if the API itself is up.

### Common issues

| Problem | Fix |
|:--------|:----|
| `Connection refused` on the frontend | Backend is not running — start it with the commands above |
| `ollama: command not found` | Install Ollama from [https://ollama.com](https://ollama.com) |
| `model not found` error | Run `ollama pull llama3.2` to download the model |
| Port 8000 already in use | Run `python -m uvicorn main:app --port 8001` and update the API URL field in the page |
| Slow rewriting | Expected on CPU — llama3.2 takes tens of seconds to several minutes per run without a GPU; `/rewrite` (V1) is markedly slower than `/rewrite-v2` |

---

## API Endpoints

| Method | Endpoint | Description |
|:-------|:---------|:------------|
| `POST` | `/rewrite` | Rewrite plain text — **V1 pipeline**, 5 stages |
| `POST` | `/rewrite-v2` | Rewrite plain text — **V2 pipeline**, 4 stages, faster |
| `POST` | `/rewrite-and-evaluate` | Rewrite (V1) + score in one call |
| `POST` | `/rewrite-and-evaluate-v2` | Rewrite (V2) + score in one call |
| `POST` | `/rewrite-file` | Rewrite uploaded `.txt`, `.md`, `.docx`, `.pdf` (uses V1) |
| `POST` | `/evaluate` | Score an existing original/rewritten pair |
| `GET` | `/health` | Health check — also reports Ollama reachability |

### Example request

```bash
curl -X POST http://localhost:8000/rewrite-v2 \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Your AI-generated text here.",
    "tone": "academic",
    "aggressiveness": 2
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

`tone` defaults to `"btech_student"` in the request schema, **but that key does not exist in the tone prompt table** — any unrecognized tone silently falls back to `formal_report`. Pass one of the values below explicitly if you want a specific voice:

| Tone | Description |
|:-----|:------------|
| `student` | Student report voice — "we", "our", contractions |
| `academic` | Research paper — hedged, first-person plural |
| `formal_report` | Human analyst style — varied lengths, natural (also the silent fallback) |
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

Each run generates 3 candidates and returns the one with the highest weighted HLS, scored across 5 dimensions:

| Metric | Weight | What it measures |
|:-------|:------:|:----------------|
| Burstiness | 35% | Sentence length variation |
| Readability | 35% | Flesch reading ease (target 60–70) |
| Coherence | 10% | Logical flow between sentences |
| Connector density | 10% | Natural transition word usage |
| Semantic similarity | 10% | Meaning preserved vs original |

`evaluation/ai_phrase_detector.py` additionally flags known AI-typical phrases (e.g. "delve", "tapestry", "it is important to note") as a quality filter — it does not contribute to the weighted score above.

---

## Benchmark Suite

10 AI-generated sample texts across 5 domains, in `tests/samples/`:

| Domain | Files | Tone used |
|:-------|:-----:|:----------|
| Academic | 3 | `academic` |
| Blog | 2 | `conversational` |
| Technical | 2 | `technical` |
| Business | 2 | `formal_professional` |
| Healthcare | 1 | `formal_report` |

Run one manually:

```bash
curl -X POST http://localhost:8000/rewrite-and-evaluate \
  -H "Content-Type: application/json" \
  -d '{
    "text": "'"$(cat tests/samples/academic_01.txt)"'",
    "tone": "academic",
    "aggressiveness": 2
  }'
```

Results are tracked in [`tests/benchmark_notes.md`](./tests/benchmark_notes.md); the full V1-vs-V2 comparison is in [`PIPELINE_COMPARISON.md`](./PIPELINE_COMPARISON.md).

---

## Configuration

**Change LLM model** — in `pipeline/style_rewriter.py` and `pipeline/flow_smoother.py`:

```python
MODEL_NAME = "llama3.2:latest"   # or: mistral, gemma, phi3, etc.
```

**Change number of candidates** — in `pipeline/pipeline_controller.py` and `pipeline/pipeline_controller_v2.py`:

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
│   ├── pipeline_controller.py       # V1 — 5 stages, used by /rewrite
│   └── pipeline_controller_v2.py    # V2 — 4 stages, used by /rewrite-v2
├── tests/
│   ├── samples/
│   │   └── academic_01.txt … healthcare_01.txt
│   └── benchmark_notes.md
├── shared_models.py
├── main.py
├── index.html
├── requirements.txt
├── run.bat
├── TECH_STACK.md
└── PIPELINE_COMPARISON.md
```

---

## Tech Stack

See [TECH_STACK.md](./TECH_STACK.md) for the full architecture breakdown.

---

## License

MIT
# flowWrite--ai-text-humanizer
