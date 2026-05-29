"""
shared_models.py
"""

import spacy
from sentence_transformers import SentenceTransformer

# Load spaCy once
nlp = spacy.load("en_core_web_sm")

# Load SBERT once
sbert = SentenceTransformer("all-MiniLM-L6-v2")
