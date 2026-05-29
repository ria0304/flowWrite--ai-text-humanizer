"""
pipeline/pipeline_controller.py


"""

from pipeline.chunker import chunk_text
from pipeline.semantic_merge import semantic_merge
from pipeline.style_rewriter import style_rewrite
from pipeline.flow_smoother import flow_smooth
import logging

logger = logging.getLogger(__name__)

# FIX #9 — Hard cap on input size
MAX_WORDS = 5000


async def run_pipeline(text: str, tone: str, aggressiveness: int) -> dict:
    """
    Master pipeline controller.
    Runs all 4 stages and returns intermediate + final results.

    Stages:
    1. Chunk     → break text into sentence groups
    2. Merge     → combine semantically related sentences
    3. Rewrite   → LLM style rewrite with tone + aggressiveness
    4. Smooth    → final flow and transition pass

    Raises:
        ValueError: if input exceeds MAX_WORDS
    """

    # FIX #9 — Validate input length before processing
    word_count = len(text.split())
    if word_count > MAX_WORDS:
        raise ValueError(
            f"Input too long: {word_count} words. "
            f"Maximum allowed is {MAX_WORDS} words. "
            f"Please split your text into smaller sections."
        )

    if word_count < 5:
        raise ValueError("Input too short. Please provide at least a few sentences.")

    stages = {}

    # Stage 1: Chunk
    logger.info(f"Stage 1: Chunking {word_count} words...")
    chunks = chunk_text(text, chunk_size=3)
    stages["chunked"] = [" | ".join(c) for c in chunks]
    logger.info(f"  → {len(chunks)} chunks created")

    # Stage 2: Semantic Merge
    logger.info("Stage 2: Semantic merge...")
    merged = semantic_merge(chunks)
    stages["merged"] = merged
    logger.info(f"  → {len(merged)} units after merge")

    # Stage 3: Style Rewrite
    logger.info(f"Stage 3: Style rewrite (tone={tone}, aggressiveness={aggressiveness})...")
    rewritten_parts = await style_rewrite(merged, tone, aggressiveness)
    rewritten_joined = "\n\n".join(rewritten_parts)
    stages["rewritten"] = rewritten_joined

    # Stage 4: Flow Smoothing
    logger.info("Stage 4: Flow smoothing...")
    final = await flow_smooth(rewritten_joined)
    stages["smoothed"] = final

    logger.info("Pipeline complete.")

    return {
        "final": final,
        "stages": stages
    }
