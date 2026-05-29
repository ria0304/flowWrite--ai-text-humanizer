import re

# Transition/connector words commonly used in human academic writing
CONNECTORS = [
    # Contrast
    "however", "although", "even though", "while", "whereas", "on the other hand",
    "despite", "nevertheless", "yet", "but",
    # Addition
    "additionally", "furthermore", "moreover", "in addition", "also", "besides",
    # Cause/Effect
    "therefore", "thus", "consequently", "as a result", "because", "since",
    "this means", "which means", "this is because", "this helps",
    # Sequence
    "initially", "subsequently", "finally", "first", "then", "next",
    # Elaboration
    "specifically", "in particular", "for example", "for instance", "such as",
    "especially", "notably",
    # Summary
    "overall", "in summary", "ultimately", "in essence",
    # Student voice markers
    "we found", "we observed", "in this project", "our approach", "we used",
    "we built", "we implemented", "this allows", "this enables"
]

def connector_density(text: str) -> dict:
    """
    Measures how many human-like transition words and connectors are present.
    
    Returns:
        score: 0-1 normalized score
        count: raw number of connectors found
        found: list of connectors detected
        density: connectors per 100 words
    """
    text_lower = text.lower()
    words = text.split()
    word_count = max(len(words), 1)

    found = []
    for connector in CONNECTORS:
        if re.search(r'\b' + re.escape(connector) + r'\b', text_lower):
            found.append(connector)

    count = len(found)
    density = (count / word_count) * 100

    # Ideal: 3-8 connectors per 100 words for student writing
    if density >= 3.0:
        score = min(density / 8.0, 1.0)
    else:
        score = density / 3.0  # penalize too few connectors

    return {
        "score": round(score, 3),
        "count": count,
        "found": found,
        "density": round(density, 2)
    }
