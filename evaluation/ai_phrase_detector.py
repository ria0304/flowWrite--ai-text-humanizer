"""
evaluation/ai_phrase_detector.py

"""

import re

# Phrases that strongly indicate AI-generated text
# Grouped by category for maintainability
AI_PHRASES = [
    # Classic LLM filler openers
    "it is worth noting",
    "it is important to note",
    "it should be noted",
    "it is imperative",
    "it can be observed",
    "it is evident",
    "it is clear that",
    "needless to say",

    # Overused transitions
    "furthermore",
    "moreover",
    "subsequently",
    "in conclusion",
    "to summarize",
    "in summary",
    "to conclude",
    "lastly",

    # Robotic academic fillers
    "delve into",
    "delve deeper",
    "shed light on",
    "it is crucial",
    "plays a crucial role",
    "plays a pivotal role",
    "of utmost importance",
    "in the realm of",
    "in the field of",
    "tapestry",
    "nuanced",
    "multifaceted",
    "paradigm",
    "leverage",
    "utilize",
    "facilitate",
    "endeavor",
    "commence",
    "terminate",

    # Overly formal constructions
    "in order to",
    "due to the fact that",
    "with regard to",
    "with respect to",
    "in terms of",
    "it is recommended that",
    "one may argue",
    "it can be argued",

    # ChatGPT-specific patterns
    "certainly",
    "absolutely",
    "of course",
    "I'd be happy to",
    "as an AI",
    "as a language model",
    "I cannot be the only one",
]


def detect_ai_phrases(text: str) -> dict:
    """
    Detects AI-sounding phrases in text.

    Returns:
        count:       total number of AI phrases found
        found:       dict of {phrase: occurrences}
        penalty:     0-1 penalty score (higher = more AI-like)
        is_clean:    True if no AI phrases detected
        assessment:  human-readable label
    """
    text_lower = text.lower()
    words = text.split()
    word_count = max(len(words), 1)

    found = {}
    total_count = 0

    for phrase in AI_PHRASES:
        matches = re.findall(r'\b' + re.escape(phrase) + r'\b', text_lower)
        if matches:
            found[phrase] = len(matches)
            total_count += len(matches)

    # Penalty: scale by density per 100 words
    # 0 phrases = 0 penalty, 3+ per 100 words = max penalty
    density = (total_count / word_count) * 100
    penalty = min(density / 3.0, 1.0)

    if total_count == 0:
        assessment = "Clean — no AI phrases detected"
    elif total_count <= 2:
        assessment = "Mostly clean — minor AI phrases"
    elif total_count <= 5:
        assessment = "Some AI phrases — needs more rewriting"
    else:
        assessment = "Heavy AI phrasing — rewrite more aggressively"

    return {
        "count": total_count,
        "found": found,
        "penalty": round(penalty, 3),
        "is_clean": total_count == 0,
        "assessment": assessment
    }
