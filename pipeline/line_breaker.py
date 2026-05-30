"""
pipeline/line_breaker.py
Stage 5 — Invisible sentence fragmentation.
Splits sentences at natural points using zero-width spaces and soft line breaks
to confuse AI detector tokenizers without affecting visual rendering.
"""
import re

# Zero-width space (invisible in most renderers)
ZWSP = "\u200b"
# Soft hyphen (invisible unless line breaks there)
SHY = "\u00ad"


def fragment_sentences(text: str) -> str:
    """
    Inserts invisible unicode characters mid-sentence at natural break points.
    Visually the text looks identical but detectors tokenize it differently.
    """
    sentences = re.split(r'(?<=[.!?])\s+', text)
    fragmented = []

    for sentence in sentences:
        words = sentence.split()
        if len(words) < 6:
            fragmented.append(sentence)
            continue

        new_sentence = ""
        for i, word in enumerate(words):
            if i == 0:
                new_sentence += word
            elif word.lower() in ("and", "but", "so", "because", "which", "that", "when", "while", "although", "however"):
                # Insert zero-width space before connector words
                new_sentence += " " + ZWSP + word
            elif "," in word and i > 2:
                # Insert soft break after comma
                new_sentence += " " + word + SHY
            else:
                new_sentence += " " + word

        fragmented.append(new_sentence)

    return "\n".join(fragmented)


def inject_invisible_breaks(text: str) -> str:
    """
    Injects zero-width spaces at strategic positions throughout the text.
    Targets the boundary between clauses and long noun phrases.
    """
    # After opening clause patterns
    text = re.sub(
        r'(In practice|That said|Which means|And that means|So when|But when|Even though|Given that)',
        r'\1' + ZWSP,
        text
    )

    # Before long noun phrases (after 'the')
    text = re.sub(r'\bthe ([a-z])', lambda m: f"the {ZWSP}{m.group(1)}", text)

    # Mid-sentence after semicolons
    text = re.sub(r';(\s)', r';' + ZWSP + r'\1', text)

    return text


def apply_line_break_trick(text: str) -> str:
    """Full pipeline for the line break bypass trick."""
    text = fragment_sentences(text)
    text = inject_invisible_breaks(text)
    return text
