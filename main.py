from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pipeline.pipeline_controller import run_pipeline
from evaluation.hls import compute_hls
import logging
import io

# Optional file parsing libraries — install as needed
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

app = FastAPI(title="Discourse Rewriter API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class RewriteRequest(BaseModel):
    text: str
    tone: str = "btech_student"  # btech_student | formal_report | casual
    aggressiveness: int = 2       # 1 = light, 2 = medium, 3 = heavy

class RewriteResponse(BaseModel):
    original: str
    rewritten: str
    stages: dict  # intermediate outputs per stage

@app.post("/rewrite", response_model=RewriteResponse)
async def rewrite(req: RewriteRequest):
    if not req.text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty.")
    try:
        result = await run_pipeline(req.text, req.tone, req.aggressiveness)
        return RewriteResponse(
            original=req.text,
            rewritten=result["final"],
            stages=result["stages"]
        )
    except Exception as e:
        logger.error(f"Pipeline error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


def extract_text_from_file(filename: str, content: bytes) -> str:
    """Extract plain text from .txt, .md, .docx, or .pdf uploads."""
    ext = filename.rsplit(".", 1)[-1].lower()

    if ext in ("txt", "md"):
        return content.decode("utf-8", errors="replace")

    elif ext == "docx":
        if not DOCX_AVAILABLE:
            raise HTTPException(
                status_code=422,
                detail="python-docx is not installed. Run: pip install python-docx"
            )
        doc = python_docx.Document(io.BytesIO(content))
        return "\n".join(p.text for p in doc.paragraphs if p.text.strip())

    elif ext == "pdf":
        if not PDF_AVAILABLE:
            raise HTTPException(
                status_code=422,
                detail="pdfplumber is not installed. Run: pip install pdfplumber"
            )
        text_parts = []
        with pdfplumber.open(io.BytesIO(content)) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)
        return "\n".join(text_parts)

    else:
        raise HTTPException(
            status_code=415,
            detail=f"Unsupported file type: .{ext}. Supported: .txt, .md, .docx, .pdf"
        )


@app.post("/rewrite-file")
async def rewrite_file(
    file: UploadFile = File(...),
    tone: str = Form("btech_student"),
    aggressiveness: int = Form(2),
):
    """Accept a file upload (.txt, .md, .docx, .pdf), extract its text, and run the rewrite pipeline."""
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
    except Exception as e:
        logger.error(f"Pipeline error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

class EvaluateRequest(BaseModel):
    original: str
    rewritten: str

@app.post("/evaluate")
async def evaluate(req: EvaluateRequest):
    if not req.original.strip() or not req.rewritten.strip():
        raise HTTPException(status_code=400, detail="Both original and rewritten text required.")
    try:
        result = compute_hls(req.original, req.rewritten)
        return result
    except Exception as e:
        logger.error(f"Evaluation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
def health():
    return {"status": "ok"}
