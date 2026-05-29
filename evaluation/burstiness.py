import spacy
import numpy as np

nlp = spacy.load("en_core_web_sm")

def burstiness_score(text: str) -> dict:
    """
    Measures sentence length variation.
    Higher variance = more human-like writing.
    
    Returns:
        score: 0-1 normalized burstiness
        lengths: list of sentence lengths
        std_dev: raw standard deviation
        mean_len: average sentence length
    """
    doc = nlp(text)
    sentences = [sent.text.strip() for sent in doc.sents if sent.text.strip()]

    if len(sentences) < 2:
        return {"score": 0.0, "lengths": [], "std_dev": 0.0, "mean_len": 0.0, "sentence_count": len(sentences)}

    lengths = [len(sent.split()) for sent in sentences]
    mean_len = float(np.mean(lengths))
    std_dev = float(np.std(lengths))

    # Normalize: typical human writing has std_dev of 8-15 words
    # We normalize against 15 as "ideal human" burstiness
    score = min(std_dev / 15.0, 1.0)

    return {
        "score": round(score, 3),
        "lengths": lengths,
        "std_dev": round(std_dev, 2),
        "mean_len": round(mean_len, 2),
        "sentence_count": len(sentences)
    }
