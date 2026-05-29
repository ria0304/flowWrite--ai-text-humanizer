import spacy
import numpy as np

nlp = spacy.load("en_core_web_sm")

def count_syllables(word: str) -> int:
    """Simple syllable counter."""
    word = word.lower().strip(".,!?;:")
    if len(word) <= 3:
        return 1
    vowels = "aeiouy"
    count = 0
    prev_vowel = False
    for char in word:
        is_vowel = char in vowels
        if is_vowel and not prev_vowel:
            count += 1
        prev_vowel = is_vowel
    if word.endswith("e"):
        count -= 1
    return max(1, count)


def readability_scores(text: str) -> dict:
    """
    Computes:
    - Flesch Reading Ease (higher = easier, 60-70 = student level)
    - Flesch-Kincaid Grade Level (ideal: 10-14 for college)
    - Balance score: how close to ideal student writing range
    
    Returns:
        flesch_ease: 0-100 score
        fk_grade: grade level number
        balance_score: 0-1 (how close to ideal student range)
        assessment: human-readable label
    """
    doc = nlp(text)
    sentences = [s for s in doc.sents if s.text.strip()]
    words = [t for t in doc if not t.is_punct and not t.is_space]

    if not sentences or not words:
        return {"flesch_ease": 0, "fk_grade": 0, "balance_score": 0, "assessment": "insufficient text"}

    num_sentences = len(sentences)
    num_words = len(words)
    num_syllables = sum(count_syllables(w.text) for w in words)

    # Flesch Reading Ease
    flesch = 206.835 - 1.015 * (num_words / num_sentences) - 84.6 * (num_syllables / num_words)
    flesch = max(0, min(100, flesch))

    # Flesch-Kincaid Grade Level
    fk_grade = 0.39 * (num_words / num_sentences) + 11.8 * (num_syllables / num_words) - 15.59

    # Balance score: ideal BTech report = Flesch 40-65, FK grade 10-14
    # Score 1.0 if perfectly in range, decreasing outside
    flesch_ideal = 52.5  # midpoint of 40-65
    flesch_distance = abs(flesch - flesch_ideal) / 52.5
    balance_score = max(0.0, 1.0 - flesch_distance)

    # Assessment label
    if flesch >= 70:
        assessment = "Too simple (below college level)"
    elif flesch >= 50:
        assessment = "Good — college / student level"
    elif flesch >= 30:
        assessment = "Formal academic tone"
    else:
        assessment = "Very complex / dense"

    return {
        "flesch_ease": round(flesch, 2),
        "fk_grade": round(fk_grade, 2),
        "balance_score": round(balance_score, 3),
        "assessment": assessment
    }
