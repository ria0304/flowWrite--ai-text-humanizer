from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

# Load once at module level
model = SentenceTransformer("all-MiniLM-L6-v2")

SIMILARITY_THRESHOLD = 0.55  # tune this — higher = only merge very similar sentences

def merge_chunk(sentences: list[str]) -> list[str]:
    """
    Step 2: Semantic Merge
    - Embed each sentence
    - Merge highly similar adjacent sentences into one idea unit
    - Returns list of merged sentence groups (as strings joined by space)
    """
    if len(sentences) <= 1:
        return sentences

    embeddings = model.encode(sentences)
    merged = []
    i = 0

    while i < len(sentences):
        if i + 1 < len(sentences):
            sim = cosine_similarity(
                [embeddings[i]], [embeddings[i + 1]]
            )[0][0]

            if sim >= SIMILARITY_THRESHOLD:
                # Merge these two sentences into one unit
                merged.append(sentences[i] + " " + sentences[i + 1])
                i += 2  # skip next since we merged it
            else:
                merged.append(sentences[i])
                i += 1
        else:
            merged.append(sentences[i])
            i += 1

    return merged


def semantic_merge(chunks: list[list[str]]) -> list[str]:
    """
    Run semantic merge on all chunks.
    Returns flat list of merged sentence units.
    """
    merged_all = []
    for chunk in chunks:
        merged = merge_chunk(chunk)
        merged_all.extend(merged)
    return merged_all
