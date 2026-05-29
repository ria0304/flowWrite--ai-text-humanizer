from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

sbert = SentenceTransformer("all-MiniLM-L6-v2")

def semantic_similarity(original: str, rewritten: str) -> dict:
    """
    Measures how much meaning is preserved between original and rewritten text.
    Uses SBERT document-level embeddings.

    Score interpretation:
        > 0.85 → meaning well preserved
        0.65-0.85 → moderate preservation (acceptable)
        < 0.65 → too much meaning lost

    Returns:
        score: 0-1 cosine similarity
        preserved: bool (True if > 0.65)
        label: human-readable assessment
    """
    if not original.strip() or not rewritten.strip():
        return {"score": 0.0, "preserved": False, "label": "Empty input"}

    emb_orig = sbert.encode([original])
    emb_new = sbert.encode([rewritten])

    score = float(cosine_similarity(emb_orig, emb_new)[0][0])

    if score >= 0.85:
        label = "Meaning well preserved"
    elif score >= 0.65:
        label = "Meaning mostly preserved"
    else:
        label = "Meaning significantly altered"

    return {
        "score": round(score, 3),
        "preserved": score >= 0.65,
        "label": label
    }
