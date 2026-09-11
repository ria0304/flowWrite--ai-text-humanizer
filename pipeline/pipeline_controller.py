"""
pipeline/pipeline_controller.py
"""
import logging
from pipeline.chunker import chunk_text
from pipeline.semantic_merge import semantic_merge
from pipeline.style_rewriter import style_rewrite
from pipeline.flow_smoother import flow_smooth
from pipeline.line_breaker import apply_line_break_trick
from evaluation.hls import compute_hls

logger = logging.getLogger(__name__)

MAX_WORDS = 5000
NUM_CANDIDATES = 3

def _quality_score(hls_result: dict) -> float:
    dims = hls_result["dimensions"]
    return round(
        0.35 * dims["burstiness"]["score"]      # was 0.20
        + 0.10 * dims["coherence"]["score"]     # was 0.30
        + 0.35 * dims["readability"]["score"]   # was 0.20
        + 0.10 * dims["connectors"]["score"]
        + 0.10 * dims["similarity"]["score"],   # was 0.20
        3,
    )

async def run_pipeline(
    text: str,
    tone: str = "formal_report",
    aggressiveness: int = 2,
    enable_stage5: bool = True
) -> dict:
    """
    Run the full FlowWrite pipeline.
    
    Args:
        text: Input text to process
        tone: Writing tone for rewriting
        aggressiveness: Aggressiveness level for rewriting (1-3)
        enable_stage5: If True, apply Stage 5 (Line Break Fragmentation).
                      If False, skip Stage 5 for ablation studies.
    
    Returns:
        Dictionary containing final text, stage information, and evaluation
    """
    word_count = len(text.split())
    if word_count > MAX_WORDS:
        raise ValueError(f"Input too long: {word_count} words. Maximum is {MAX_WORDS} words.")

    logger.info(f"Pipeline start: {word_count} words")

    # Stage 1 — Chunking
    logger.info("Stage 1: Chunking...")
    chunks = chunk_text(text)
    logger.info(f"  → {len(chunks)} chunks created")

    # Stage 2 — Semantic merge
    logger.info("Stage 2: Semantic merge...")
    merged = semantic_merge(chunks)
    logger.info(f"  → {len(merged)} units after merge")

    # Stage 3 + 4 — Generate and score candidates
    logger.info(f"Stage 3: Generating {NUM_CANDIDATES} rewrite candidate(s)...")
    candidates = []
    for _ in range(NUM_CANDIDATES):
        rewritten = await style_rewrite(merged, tone, aggressiveness)
        combined = "\n\n".join(rewritten)
        smoothed = await flow_smooth(combined)
        candidates.append(smoothed)

    best_text = text
    best_score = -1.0
    best_eval = None

    logger.info("Stage 4: Selecting best candidate...")
    for candidate in candidates:
        evaluation = compute_hls(text, candidate)
        score = _quality_score(evaluation)
        if score > best_score:
            best_score = score
            best_text = candidate
            best_eval = evaluation

    logger.info(f"Best candidate score: {best_score}")

    # Stage 5 — Line break fragmentation (optional for ablation studies)
    if enable_stage5:
        logger.info("Stage 5: Line break fragmentation...")
        final = apply_line_break_trick(best_text)
        stage5_applied = True
    else:
        logger.info("Stage 5: SKIPPED (ablation study)")
        final = best_text
        stage5_applied = False

    logger.info("Pipeline complete.")

    return {
        "final": final,
        "stages": {
            "chunking": f"{len(chunks)} chunks created",
            "semantic_merge": f"{len(merged)} units after merge",
            "candidates": f"{NUM_CANDIDATES} candidates generated",
            "selection": "best candidate selected by quality score",
            "line_break_fragmentation": "done" if stage5_applied else "skipped",
        },
        "stage5_applied": stage5_applied,
        "evaluation": best_eval,
        "best_score": best_score,
    }
