from pipeline.chunker import chunk_text
from pipeline.semantic_merge import semantic_merge
from pipeline.style_rewriter import style_rewrite
from pipeline.flow_smoother import flow_smooth
import logging

logger = logging.getLogger(__name__)


async def run_pipeline(text: str, tone: str, aggressiveness: int) -> dict:
    """
    Master pipeline controller.
    Runs all 4 stages and returns intermediate + final results.

    Stages:
    1. Chunk     → break text into sentence groups
    2. Merge     → combine semantically related sentences
    3. Rewrite   → LLM style rewrite with tone + aggressiveness
    4. Smooth    → final flow and transition pass
    """
    stages = {}

    # ── Stage 1: Chunk ──────────────────────────────────────────
    logger.info("Stage 1: Chunking...")
    chunks = chunk_text(text, chunk_size=3)
    stages["chunked"] = [" | ".join(c) for c in chunks]

    # ── Stage 2: Semantic Merge ──────────────────────────────────
    logger.info("Stage 2: Semantic merge...")
    merged = semantic_merge(chunks)
    stages["merged"] = merged

    # ── Stage 3: Style Rewrite ───────────────────────────────────
    logger.info("Stage 3: Style rewrite...")
    rewritten_parts = await style_rewrite(merged, tone, aggressiveness)
    rewritten_joined = "\n\n".join(rewritten_parts)
    stages["rewritten"] = rewritten_joined

    # ── Stage 4: Flow Smoothing ──────────────────────────────────
    logger.info("Stage 4: Flow smoothing...")
    final = await flow_smooth(rewritten_joined)
    stages["smoothed"] = final

    return {
        "final": final,
        "stages": stages
    }
