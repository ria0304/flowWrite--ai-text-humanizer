"""
evaluation/burstiness.py

"""

import numpy as np
from shared_models import nlp


def burstiness_score(text: str) -> dict:
    """
    Measures sentence length variation.
    Higher variance = more human-like writing.

    Returns:
        score:          0-1 normalized burstiness
        lengths:        list of sentence word counts
        std_dev:        raw standard deviation
        mean_len:       average sentence length
        sentence_count: number of sentences
    """
    doc = nlp(text)
    sentences = [sent.text.strip() for sent in doc.sents if sent.text.strip()]

    if len(sentences) < 2:
        return {
            "score": 0.0,
            "lengths": [],
            "std_dev": 0.0,
            "mean_len": 0.0,
            "sentence_count": len(sentences)
        }

    lengths = [len(sent.split()) for sent in sentences]
    mean_len = float(np.mean(lengths))
    std_dev = float(np.std(lengths))

    # FIX: Use Coefficient of Variation (CV = std/mean) instead of fixed /15.0
    # CV naturally scales with text length and sentence count.
    # Typical human writing CV is around 0.4-0.6
    # We normalize against 0.5 as the "ideal human" target
    if mean_len == 0:
        score = 0.0
    else:
        cv = std_dev / mean_len
        score = min(cv / 0.5, 1.0)

    return {
        "score": round(score, 3),
        "lengths": lengths,
        "std_dev": round(std_dev, 2),
        "mean_len": round(mean_len, 2),
        "sentence_count": len(sentences)
    }
