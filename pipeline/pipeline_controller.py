"""
pipeline/pipeline_controller.py
"""
import logging
from pipeline.chunker import chunk_text
from pipeline.semantic_merge import semantic_merge
from pipeline.style_rewriter import style_rewrite
from pipeline.flow_smoother import flow_smooth
from pipeline.turnitin_bypass import turnitin_bypass

logger = logging.getLogger(__name__)

MAX_WORDS = 5000

async def run_pipeline(text: str, tone: str = "formal_report", aggressiveness: int = 2) -> dict:
    word_count = len(text.split())
    if word_count > MAX_WORDS:
        raise ValueError(f"Input too long: {word_count} words. Maximum is {MAX_WORDS} words.")

    # Stage 1 — Chunking
    logger.info(f"Stage 1: Chunking {word_count} words...")
    chunks = chunk_text(text)
    logger.info(f"  → {len(chunks)} chunks created")

    # Stage 2 — Semantic merge
    logger.info("Stage 2: Semantic merge...")
    merged = semantic_merge(chunks)
    logger.info(f"  → {len(merged)} units after merge")

    # Stage 3 — Style rewrite
    logger.info(f"Stage 3: Style rewrite (tone={tone}, aggressiveness={aggressiveness})...")
    rewritten = await style_rewrite(merged, tone, aggressiveness)

    # Stage 4 — Flow smoothing
    logger.info("Stage 4: Flow smoothing...")
    combined = "\n\n".join(rewritten)
    smoothed = await flow_smooth(combined)

    # Stage 5 — Turnitin bypass
    logger.info("Stage 5: Turnitin bypass...")
    final = await turnitin_bypass(smoothed)

    logger.info("Pipeline complete.")

    return {
        "final": final,
        "stages": {
            "chunking": f"{len(chunks)} chunks created",
            "semantic_merge": f"{len(merged)} units after merge",
            "style_rewrite": f"{len(rewritten)} segments rewritten",
            "flow_smoothing": "done",
            "turnitin_bypass": "done"
        }
    }
