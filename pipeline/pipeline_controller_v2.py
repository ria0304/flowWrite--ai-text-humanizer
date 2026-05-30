"""
pipeline/pipeline_controller_v2.py
Simplified pipeline — no flow smoother stage.
Used for Day 2 benchmark comparison against v1.
"""
import logging
import time
from pipeline.chunker import chunk_text
from pipeline.semantic_merge import semantic_merge
from pipeline.style_rewriter import style_rewrite
from pipeline.line_breaker import apply_line_break_trick
from evaluation.hls import compute_hls

logger = logging.getLogger(__name__)

MAX_WORDS = 5000
NUM_CANDIDATES = 3


def _quality_score(hls_result: dict) -> float:
    dims = hls_result["dimensions"]
    return round(
        0.35 * dims["burstiness"]["score"]
        + 0.10 * dims["coherence"]["score"]
        + 0.35 * dims["readability"]["score"]
        + 0.10 * dims["connectors"]["score"]
        + 0.10 * dims["similarity"]["score"],
        3,
    )


async def run_pipeline_v2(text: str, tone: str = "formal_report", aggressiveness: int = 2) -> dict:
    """
    Simplified 4-stage pipeline (no flow smoother).
    Compare speed and quality against run_pipeline in pipeline_controller.py.
    """
    start_time = time.time()

    word_count = len(text.split())
    if word_count > MAX_WORDS:
        raise ValueError(f"Input too long: {word_count} words. Maximum is {MAX_WORDS} words.")

    logger.info(f"[V2] Pipeline start: {word_count} words")

    # Stage 1 — Chunking
    logger.info("[V2] Stage 1: Chunking...")
    chunks = chunk_text(text)
    logger.info(f"[V2]   → {len(chunks)} chunks created")

    # Stage 2 — Semantic merge
    logger.info("[V2] Stage 2: Semantic merge...")
    merged = semantic_merge(chunks)
    logger.info(f"[V2]   → {len(merged)} units after merge")

    # Stage 3 — Generate candidates (no flow smoother)
    logger.info(f"[V2] Stage 3: Generating {NUM_CANDIDATES} rewrite candidate(s)...")
    candidates = []
    for _ in range(NUM_CANDIDATES):
        rewritten = await style_rewrite(merged, tone, aggressiveness)
        combined = "\n\n".join(rewritten)
        candidates.append(combined)

    # Stage 4 — Select best candidate
    best_text = text
    best_score = -1.0
    best_eval = None

    logger.info("[V2] Stage 4: Selecting best candidate...")
    for candidate in candidates:
        evaluation = compute_hls(text, candidate)
        score = _quality_score(evaluation)
        if score > best_score:
            best_score = score
            best_text = candidate
            best_eval = evaluation

    logger.info(f"[V2] Best candidate score: {best_score}")

    # Stage 5 — Line break fragmentation
    logger.info("[V2] Stage 5: Line break fragmentation...")
    final = apply_line_break_trick(best_text)

    elapsed = round(time.time() - start_time, 2)
    logger.info(f"[V2] Pipeline complete in {elapsed}s")

    return {
        "final": final,
        "stages": {
            "chunking": f"{len(chunks)} chunks created",
            "semantic_merge": f"{len(merged)} units after merge",
            "candidates": f"{NUM_CANDIDATES} candidates generated",
            "selection": "best candidate selected by quality score",
            "line_break_fragmentation": "done",
        },
        "evaluation": best_eval,
        "best_score": best_score,
        "processing_time_seconds": elapsed,
    }
