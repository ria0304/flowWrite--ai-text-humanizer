# FlowWrite — Tech Stack

---

## Frontend (Client-Side)

**Framework:** Vanilla HTML + CSS + JavaScript (no framework, no bundler)

**UI Features:**
- Single-page app with tabbed input (type/paste or file upload)
- Drag-and-drop file upload with real-time feedback
- Live Human Likeness Score dashboard with animated metric bars
- Responsive layout — works on desktop and mobile

**Fonts:** Crimson Pro (serif body), DM Sans (UI), JetBrains Mono (labels/metrics)

**Hosting:** AWS S3 (static website) + CloudFront CDN (HTTPS, global edge caching)

---

## Backend (Server-Side)

**Framework:** FastAPI (Python 3.11+)

**Server:** Uvicorn (ASGI)

**Key Endpoints:**
- `POST /rewrite` — Rewrites plain text through the full pipeline
- `POST /rewrite-file` — Accepts `.txt`, `.md`, `.docx`, `.pdf` uploads
- `POST /evaluate` — Scores original vs rewritten text using HLS metrics
- `POST /rewrite-and-evaluate` — Rewrite + score in a single call
- `GET /health` — Reports API and Ollama status

**File Parsing:** pdfplumber (PDF extraction), python-docx (DOCX extraction)

**Hosting:** AWS EC2 m7i-flex.large (2 vCPU, 8GB RAM, Ubuntu 26.04 LTS), managed by systemd for auto-restart on reboot

---

## NLP Pipeline

FlowWrite runs text through 5 sequential stages, generating 3 candidates per run and selecting the best using Human Likeness Score (HLS).

### Stage 1 — Chunker
`pipeline/chunker.py`

spaCy (`en_core_web_sm`) segments input text into sentence-level groups. Groups are sized to fit within the LLM's effective context window for consistent rewrites.

### Stage 2 — Semantic Merge
`pipeline/semantic_merge.py`

SBERT (`all-MiniLM-L6-v2`) generates sentence embeddings and merges semantically related chunks using cosine similarity thresholding. This ensures the LLM rewrites coherent units rather than isolated fragments.

### Stage 3 — Style Rewriter
`pipeline/style_rewriter.py`

Ollama (llama3.2) rewrites each merged unit with the selected tone and aggressiveness level. Generates 3 candidates per unit. Prompts ban AI-typical phrases, enforce pronoun subjects, and target a Flesch reading ease of 60–70.

### Stage 4 — Flow Smoother
`pipeline/flow_smoother.py`

A second Ollama pass smooths sentence rhythm, adds natural transitions, and removes formality creep introduced during rewriting. Also strips model leakage artifacts like `(Note: ...)` annotations.

### Stage 5 — Line Break Fragmentation
`pipeline/line_breaker.py`

Injects invisible Unicode zero-width characters between tokens at strategic positions. This disrupts detector tokenization without any visible change to the output text.

---

## AI / Models

**LLM Runtime:** Ollama — runs models locally on the EC2 instance (CPU mode, no GPU)

**Primary Model:** `llama3.2:latest` (2 GB) — used for style rewriting and flow smoothing

**Embeddings:** SBERT `all-MiniLM-L6-v2` (via sentence-transformers) — semantic similarity scoring and chunk merging

**NLP:** spaCy `en_core_web_sm` — sentence segmentation and linguistic feature extraction

---

## Evaluation — Human Likeness Score (HLS)

Every rewrite is scored across 6 dimensions. The pipeline generates 3 candidates per run and returns the one with the highest weighted HLS.

### Burstiness (35%)
`evaluation/burstiness.py`

Measures sentence length variation using standard deviation of word counts. Human writing varies dramatically in sentence length; AI writing is suspiciously uniform.

### Readability (35%)
`evaluation/readability.py`

Flesch-Kincaid reading ease score targeting 60–70 (plain English range). Also tracks Flesch-Kincaid grade level.

### Coherence (10%)
`evaluation/coherence.py`

SBERT cosine similarity between consecutive sentences. Penalises both incoherence (topic jumps) and excessive uniformity (repetitive phrasing).

### Connector Density (10%)
`evaluation/connector_density.py`

Counts natural transition words (however, therefore, meanwhile, etc.). Human writing uses connectors naturally; AI writing tends to overuse or omit them entirely.

### Semantic Similarity (10%)
`evaluation/semantic_similarity.py`

SBERT cosine similarity between the original and rewritten text. Ensures meaning is preserved during rewriting.

### AI Phrase Detector
`evaluation/ai_phrase_detector.py`

Detects and penalises known AI-typical phrases (delve, tapestry, it is important to note, etc.). Used as a quality filter rather than a weighted HLS dimension.

---

## AWS Infrastructure

**EC2:** m7i-flex.large instance (2 vCPU, 8GB RAM) running Ubuntu 26.04 LTS. Hosts FastAPI + Ollama. FastAPI managed by systemd — auto-restarts on crash or reboot.

**S3:** `flowwrite-frontend` bucket with static website hosting enabled. Stores `index.html` (31 KB). Public read access via bucket policy.

**CloudFront:** Distribution `E35B1O8DXHYISH` at `d37s95cs5nvhcl.cloudfront.net`. Routes `/*` to S3 and `/rewrite*`, `/evaluate*`, `/health*` to EC2 :8000. Handles HTTPS termination — no SSL cert needed on EC2.

**Security Group:** `launch-wizard-4` — inbound rules for SSH (My IP only), HTTP (80), HTTPS (443), and FastAPI (8000).

**IAM:** `github-actions-flowwrite` user with `AmazonS3FullAccess`, `CloudFrontFullAccess`, and `AmazonEC2FullAccess` for CI/CD operations.

---

## CI/CD

**Platform:** GitHub Actions

**Trigger:** Push to `main` branch

**Pipeline:**
1. Checkout code
2. Configure AWS credentials (via GitHub Secrets)
3. Upload `index.html` to S3 with `no-cache` header
4. Invalidate CloudFront cache (`/*`) so users always get the latest frontend

**Secrets used:** `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_REGION`, `S3_BUCKET`, `CLOUDFRONT_DISTRIBUTION_ID`

---

## Architecture Highlights

**CPU-only inference** — Ollama runs llama3.2 entirely on CPU. No GPU required, fits within 8GB RAM with headroom for the OS and FastAPI.

**Multi-candidate selection** — Pipeline generates 3 rewrite candidates per run and selects the best by HLS score rather than returning the first result.

**Zero frontend dependencies** — No npm, no bundler, no framework. The entire frontend is a single 31 KB HTML file deployable to any static host.

**Invisible unicode bypass** — Line breaker stage uses zero-width Unicode characters that are invisible to readers but disrupt AI detector tokenization pipelines.

**Systemd reliability** — FastAPI is registered as a systemd service with `Restart=always`, ensuring the backend recovers automatically from crashes or reboots.
