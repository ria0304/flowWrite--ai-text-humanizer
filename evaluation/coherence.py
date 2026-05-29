"""
evaluation/coherence.py


"""

import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from shared_models import nlp, sbert


def coherence_score(text: str) -> dict:
    """
    Measures how logically connected sentences are.
    Uses SBERT embeddings + cosine similarity between consecutive sentences.

    Higher score = better flow and connection between ideas.

    Returns:
        score:           0-1 coherence score
        pairwise_scores: similarity between each consecutive sentence pair
        avg_similarity:  mean of pairwise scores
    """
    doc = nlp(text)
    sentences = [s.text.strip() for s in doc.sents if s.text.strip()]

    if len(sentences) < 2:
        return {"score": 0.0, "pairwise_scores": [], "avg_similarity": 0.0}

    embeddings = sbert.encode(sentences)

    pairwise = []
    for i in range(len(embeddings) - 1):
        sim = cosine_similarity([embeddings[i]], [embeddings[i + 1]])[0][0]
        pairwise.append(round(float(sim), 3))

    avg_sim = float(np.mean(pairwise))

    # FIX: Raised upper bound from 0.75 to 0.85
    # Academic writing naturally has high sentence similarity (0.75-0.85)
    # Only penalize if truly repetitive (> 0.85) or truly disconnected (< 0.35)
    if avg_sim < 0.35:
        score = avg_sim / 0.35          # penalize disconnected text
    elif avg_sim <= 0.85:
        score = 1.0                     # ideal range — full score
    else:
        score = 1.0 - (avg_sim - 0.85) / 0.15  # penalize overly repetitive

    return {
        "score": round(max(0.0, score), 3),
        "pairwise_scores": pairwise,
        "avg_similarity": round(avg_sim, 3)
    }
