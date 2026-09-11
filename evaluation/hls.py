"""
evaluation/hls.py


"""

from evaluation.burstiness import burstiness_score
from evaluation.readability import readability_scores
from evaluation.coherence import coherence_score
from evaluation.semantic_similarity import semantic_similarity
from evaluation.connector_density import connector_density
from evaluation.ai_phrase_detector import detect_ai_phrases

# Weights for Human Likeness Score (HLS)
# Must sum to 1.0
WEIGHTS = {
    "burstiness":  0.20,   # sentence length variation
    "coherence":   0.25,   # logical flow (most important)
    "readability": 0.20,   # appropriate complexity level
    "connectors":  0.20,   # transition word usage
    "similarity":  0.15,   # meaning preservation (NEW)
}


def compute_hls(original: str, rewritten: str) -> dict:
    """
    Computes the full multi-dimensional Human Likeness Score (HLS).

    Returns:
        hls:                0-1 Human Likeness Score (higher = more human)
        hls_original:       HLS of the original text for comparison
        improvement:        HLS gain vs original
        interpretation:     text label
        meaning_preserved:  label from semantic similarity
        similarity_score:   raw similarity float
        ai_phrases:         detected AI phrases in rewritten text
        dimensions:         all individual metric scores (rewritten)
        original_dimensions: all individual metric scores (original)
    """

    # --- Evaluate REWRITTEN text ---
    burst = burstiness_score(rewritten)
    read  = readability_scores(rewritten)
    coher = coherence_score(rewritten)
    conn  = connector_density(rewritten)
    sim   = semantic_similarity(original, rewritten)
    ai    = detect_ai_phrases(rewritten)

    # --- Evaluate ORIGINAL text (for comparison) ---
    burst_orig = burstiness_score(original)
    read_orig  = readability_scores(original)
    coher_orig = coherence_score(original)
    conn_orig  = connector_density(original)
    ai_orig    = detect_ai_phrases(original)

    # --- Compute HLS (rewritten) ---
    hls = (
        WEIGHTS["burstiness"]  * burst["score"] +
        WEIGHTS["coherence"]   * coher["score"] +
        WEIGHTS["readability"] * read["balance_score"] +
        WEIGHTS["connectors"]  * conn["score"] +
        WEIGHTS["similarity"]  * sim["score"]       # FIX #11 — now included
    )

    # --- Compute HLS (original) ---
    hls_orig = (
        WEIGHTS["burstiness"]  * burst_orig["score"] +
        WEIGHTS["coherence"]   * coher_orig["score"] +
        WEIGHTS["readability"] * read_orig["balance_score"] +
        WEIGHTS["connectors"]  * conn_orig["score"] +
        WEIGHTS["similarity"]  * 1.0   # original vs itself = perfect similarity
    )

    improvement = round(hls - hls_orig, 3)

    # Interpretation label
    if hls >= 0.80:
        interpretation = "Strongly human-like"
    elif hls >= 0.65:
        interpretation = "Mostly human-like"
    elif hls >= 0.50:
        interpretation = "Moderate — needs more work"
    else:
        interpretation = "Still AI-like"

    return {
        "hls": round(hls, 3),
        "hls_original": round(hls_orig, 3),
        "improvement": improvement,
        "interpretation": interpretation,
        "meaning_preserved": sim["label"],
        "similarity_score": sim["score"],

        # AI phrase detection
        "ai_phrases": {
            "count": ai["count"],
            "found": ai["found"],
            "penalty": ai["penalty"]
        },
        "ai_phrases_original": {
            "count": ai_orig["count"],
            "found": ai_orig["found"]
        },

        # Rewritten text dimension scores
        "dimensions": {
            "burstiness": {
                "score": burst["score"],
                "std_dev": burst["std_dev"],
                "mean_sentence_len": burst["mean_len"],
                "sentence_count": burst["sentence_count"]
            },
            "coherence": {
                "score": coher["score"],
                "avg_similarity": coher["avg_similarity"]
            },
            "readability": {
                "score": read["balance_score"],
                "flesch_ease": read["flesch_ease"],
                "fk_grade": read["fk_grade"],
                "assessment": read["assessment"]
            },
            "connectors": {
                "score": conn["score"],
                "count": conn["count"],
                "found": conn["found"],
                "density_per_100": conn["density"]
            },
            "similarity": {
                "score": sim["score"],
                "preserved": sim["preserved"],
                "label": sim["label"]
            }
        },

        # Original text scores (for comparison table in UI)
        "original_dimensions": {
            "burstiness": burst_orig["score"],
            "coherence": coher_orig["score"],
            "readability": read_orig["balance_score"],
            "connectors": conn_orig["score"],
            "similarity": 1.0
        }
    }
