from evaluation.burstiness import burstiness_score
from evaluation.readability import readability_scores
from evaluation.coherence import coherence_score
from evaluation.semantic_similarity import semantic_similarity
from evaluation.connector_density import connector_density

# Weights for Human Likeness Score (HLS)
# Tuned for BTech student report writing
WEIGHTS = {
    "burstiness":   0.25,   # sentence length variation
    "coherence":    0.30,   # logical flow between sentences (most important)
    "readability":  0.20,   # appropriate complexity level
    "connectors":   0.25,   # use of transition words
}

def compute_hls(original: str, rewritten: str) -> dict:
    """
    Computes the full multi-dimensional evaluation.

    Returns:
        hls: Human Likeness Score (0-1, higher = more human)
        dimensions: individual scores per axis
        similarity: how much meaning was preserved
        interpretation: text label
        improvement: HLS gain vs original
    """

    # --- Evaluate REWRITTEN text ---
    burst = burstiness_score(rewritten)
    read  = readability_scores(rewritten)
    coher = coherence_score(rewritten)
    conn  = connector_density(rewritten)
    sim   = semantic_similarity(original, rewritten)

    # --- Evaluate ORIGINAL text (for comparison) ---
    burst_orig = burstiness_score(original)
    read_orig  = readability_scores(original)
    coher_orig = coherence_score(original)
    conn_orig  = connector_density(original)

    # --- Compute HLS ---
    hls = (
        WEIGHTS["burstiness"]  * burst["score"]  +
        WEIGHTS["coherence"]   * coher["score"]  +
        WEIGHTS["readability"] * read["balance_score"] +
        WEIGHTS["connectors"]  * conn["score"]
    )

    hls_orig = (
        WEIGHTS["burstiness"]  * burst_orig["score"]  +
        WEIGHTS["coherence"]   * coher_orig["score"]  +
        WEIGHTS["readability"] * read_orig["balance_score"] +
        WEIGHTS["connectors"]  * conn_orig["score"]
    )

    improvement = round(hls - hls_orig, 3)

    # Interpretation
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

        # Rewritten text scores
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
            }
        },

        # Original text scores (for comparison table)
        "original_dimensions": {
            "burstiness": burst_orig["score"],
            "coherence": coher_orig["score"],
            "readability": read_orig["balance_score"],
            "connectors": conn_orig["score"]
        }
    }
