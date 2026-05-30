from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pipeline.pipeline_controller import run_pipeline
from evaluation.hls import compute_hls
import logging
import time
import io

try:
    import docx as python_docx
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False

try:
    import pdfplumber
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="FlowWrite — Text Rewriting API",
    description="Rewrites text to improve clarity, flow, and readability.",
    version="1.2.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class RewriteRequest(BaseModel):
    text: str
    tone: str = "btech_student"
    aggressiveness: int = 2


class RewriteResponse(BaseModel):
    original: str
    rewritten: str
    stages: dict


class EvaluateRequest(BaseModel):
    original: str
    rewritten: str


@app.post("/rewrite", response_model=RewriteResponse)
async def rewrite(req: RewriteRequest):
    """Rewrite text through the full pipeline."""
    if not req.text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty.")

    if req.aggressiveness not in (1, 2, 3):
        raise HTTPException(status_code=400, detail="Aggressiveness must be 1, 2, or 3.")

    start = time.time()
    try:
        result = await run_pipeline(req.text, req.tone, req.aggressiveness)
        elapsed = round(time.time() - start, 2)
        logger.info(f"/rewrite completed in {elapsed}s")
        return RewriteResponse(
            original=req.text,
            rewritten=result["final"],
            stages=result["stages"]
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Pipeline error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/evaluate")
async def evaluate(req: EvaluateRequest):
    """Evaluate original and rewritten text using HLS metrics."""
    if not req.original.strip() or not req.rewritten.strip():
        raise HTTPException(status_code=400, detail="Both original and rewritten text required.")
    try:
        result = compute_hls(req.original, req.rewritten)
        return result
    except Exception as e:
        logger.error(f"Evaluation error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/rewrite-and-evaluate")
async def rewrite_and_evaluate(req: RewriteRequest):
    """
    Rewrite text and evaluate it in one API call.
    Returns rewritten text plus HLS evaluation scores.
    """
    if not req.text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty.")

    if req.aggressiveness not in (1, 2, 3):
        raise HTTPException(status_code=400, detail="Aggressiveness must be 1, 2, or 3.")

    start = time.time()
    try:
        result = await run_pipeline(req.text, req.tone, req.aggressiveness)
        rewritten = result["final"]
        evaluation = compute_hls(req.text, rewritten)

        elapsed = round(time.time() - start, 2)
        logger.info(f"/rewrite-and-evaluate completed in {elapsed}s")

        return {
            "original": req.text,
            "rewritten": rewritten,
            "stages": result["stages"],
            "evaluation": evaluation,
            "processing_time_seconds": elapsed
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Rewrite+evaluate error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/rewrite-file")
async def rewrite_file(
    file: UploadFile = File(...),
    tone: str = Form("btech_student"),
    aggressiveness: int = Form(2),
):
    """Upload a .txt, .md, .docx, or .pdf file and rewrite its text."""
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    try:
        text = extract_text_from_file(file.filename or "", content)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"File extraction error: {e}", exc_info=True)
        raise HTTPException(status_code=422, detail=f"Could not extract text: {e}")

    if not text.strip():
        raise HTTPException(status_code=400, detail="No text content found in file.")

    try:
        result = await run_pipeline(text, tone, aggressiveness)
        return {
            "original": text,
            "rewritten": result["final"],
            "stages": result["stages"],
            "filename": file.filename,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Pipeline error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
def health():
    """Health check endpoint."""
    return {"status": "ok", "version": "1.2.0"}


def extract_text_from_file(filename: str, content: bytes) -> str:
    """Extract plain text from .txt, .md, .docx, or .pdf uploads."""
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""

    if ext in ("txt", "md"):
        return content.decode("utf-8", errors="replace")

    if ext == "docx":
        if not DOCX_AVAILABLE:
            raise HTTPException(
                status_code=422,
                detail="python-docx not installed. Run: pip install python-docx"
            )
        doc = python_docx.Document(io.BytesIO(content))
        return "\n".join(p.text for p in doc.paragraphs if p.text.strip())

    if ext == "pdf":
        if not PDF_AVAILABLE:
            raise HTTPException(
                status_code=422,
                detail="pdfplumber not installed. Run: pip install pdfplumber"
            )
        text_parts = []
        with pdfplumber.open(io.BytesIO(content)) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)
        return "\n".join(text_parts)

    raise HTTPException(
        status_code=415,
        detail=f"Unsupported file type: .{ext}. Supported: .txt, .md, .docx, .pdf"
    )
