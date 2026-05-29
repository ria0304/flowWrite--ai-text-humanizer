"""
pipeline/chunker.py

"""

from shared_models import nlp


def chunk_text(text: str, chunk_size: int = 3) -> list[list[str]]:
    """
    Step 1: Chunk Input
    - Parse text into sentences using spaCy
    - Group sentences into chunks of `chunk_size` for context preservation
    """
    doc = nlp(text)
    sentences = [sent.text.strip() for sent in doc.sents if sent.text.strip()]

    chunks = []
    for i in range(0, len(sentences), chunk_size):
        chunk = sentences[i:i + chunk_size]
        chunks.append(chunk)

    return chunks
