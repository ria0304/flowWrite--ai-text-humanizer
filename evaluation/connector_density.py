"""
evaluation/connector_density.py


"""

import re

# Transition/connector words for human academic writing
# REMOVED: "furthermore", "subsequently", "moreover" — LLM is told to strip these
CONNECTORS = [
    # Contrast
    "however", "although", "even though", "while", "whereas",
    "on the other hand", "despite", "nevertheless", "yet", "but",
    # Addition
    "additionally", "in addition", "also", "besides",
    # Cause/Effect
    "therefore", "thus", "consequently", "as a result", "because", "since",
    "this means", "which means", "this is because", "this helps",
    # Sequence
    "initially", "finally", "first", "then", "next",
    # Elaboration
    "specifically", "in particular", "for example", "for instance",
    "such as", "especially", "notably",
    # Summary
    "overall", "in summary", "ultimately", "in essence",
    # Natural human voice markers
    "so", "that's why", "because of this", "and then", "which is why",
    # Student voice markers
    "we found", "we observed", "in this project", "our approach",
    "we used", "we built", "we implemented", "this allows", "this enables"
]


def connector_density(text: str) -> dict:
    """
    Measures how many human-like transition words and connectors are present.

    Returns:
        score:   0-1 normalized score
        count:   total number of connector occurrences (not unique types)
        found:   list of (connector, count) tuples
        density: connectors per 100 words
    """
    text_lower = text.lower()
    words = text.split()
    word_count = max(len(words), 1)

    found = {}
    total_count = 0

    for connector in CONNECTORS:
        matches = re.findall(r'\b' + re.escape(connector) + r'\b', text_lower)
        if matches:
            found[connector] = len(matches)
            total_count += len(matches)

    density = (total_count / word_count) * 100

    # Ideal: 3-8 connector occurrences per 100 words for student writing
    if density >= 3.0:
        score = min(density / 8.0, 1.0)
    else:
        score = density / 3.0  # penalize too few connectors

    return {
        "score": round(score, 3),
        "count": total_count,
        "found": found,           # now a dict: {connector: count}
        "density": round(density, 2)
    }
