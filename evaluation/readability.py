"""
evaluation/readability.py

"""

from shared_models import nlp


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
    - Flesch Reading Ease (higher = easier, 50-65 = student level)
    - Flesch-Kincaid Grade Level (ideal: 10-14 for college)
    - Balance score: 1.0 if inside ideal range, decreasing outside

    Returns:
        flesch_ease:   0-100 score
        fk_grade:      grade level number
        balance_score: 0-1 (1.0 = inside ideal range)
        assessment:    human-readable label
    """
    doc = nlp(text)
    sentences = [s for s in doc.sents if s.text.strip()]
    words = [t for t in doc if not t.is_punct and not t.is_space]

    if not sentences or not words:
        return {
            "flesch_ease": 0,
            "fk_grade": 0,
            "balance_score": 0,
            "assessment": "insufficient text"
        }

    num_sentences = len(sentences)
    num_words = len(words)
    num_syllables = sum(count_syllables(w.text) for w in words)

    # Flesch Reading Ease
    flesch = 206.835 - 1.015 * (num_words / num_sentences) - 84.6 * (num_syllables / num_words)
    flesch = max(0.0, min(100.0, flesch))

    # Flesch-Kincaid Grade Level
    fk_grade = 0.39 * (num_words / num_sentences) + 11.8 * (num_syllables / num_words) - 15.59

    # FIX: Ideal range = 40-65 Flesch for BTech/college writing
    # Score 1.0 if inside range, linearly decrease outside
    IDEAL_LOW = 40.0
    IDEAL_HIGH = 65.0

    if IDEAL_LOW <= flesch <= IDEAL_HIGH:
        balance_score = 1.0                             # perfectly in range
    elif flesch < IDEAL_LOW:
        balance_score = max(0.0, flesch / IDEAL_LOW)   # too complex
    else:
        balance_score = max(0.0, 1.0 - (flesch - IDEAL_HIGH) / 35.0)  # too simple

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
