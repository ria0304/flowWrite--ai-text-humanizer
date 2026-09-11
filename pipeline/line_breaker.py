"""
pipeline/line_breaker.py
Stage 5 — Invisible sentence fragmentation.
Splits sentences at natural points using zero-width spaces and soft line breaks
to confuse AI detector tokenizers without affecting visual rendering.
"""
import re
import unicodedata
from typing import Dict, List, Tuple, Optional

# Zero-width space (invisible in most renderers)
ZWSP = "\u200b"
# Soft hyphen (invisible unless line breaks there)
SHY = "\u00ad"


def fragment_sentences(text: str) -> Tuple[str, List[Dict]]:
    """
    Inserts invisible unicode characters mid-sentence at natural break points.
    Visually the text looks identical but detectors tokenize it differently.
    
    Returns:
        Tuple of (fragmented_text, list of perturbation records)
    """
    if not text:
        return text, []
    
    sentences = re.split(r'(?<=[.!?])\s+', text)
    fragmented = []
    perturbations = []

    for sent_idx, sentence in enumerate(sentences):
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
                pos = len(new_sentence)
                new_sentence += " " + ZWSP + word
                perturbations.append({
                    "type": "zwsp_before_connector",
                    "position": pos,
                    "character": ZWSP,
                    "context": word.lower()
                })
            elif "," in word and i > 2:
                # Insert soft break after comma
                pos = len(new_sentence) + len(word)
                new_sentence += " " + word + SHY
                perturbations.append({
                    "type": "shy_after_comma_word",
                    "position": pos,
                    "character": SHY,
                    "context": word
                })
            else:
                new_sentence += " " + word

        fragmented.append(new_sentence)

    # Join with original separator (space after punctuation), not newline
    # We need to preserve the original structure
    return " ".join(fragmented), perturbations


def inject_invisible_breaks(text: str) -> Tuple[str, List[Dict]]:
    """
    Injects zero-width spaces at strategic positions throughout the text.
    Targets the boundary between clauses and long noun phrases.
    
    Returns:
        Tuple of (modified_text, list of perturbation records)
    """
    if not text:
        return text, []
    
    perturbations = []
    
    # Track position offset due to insertions
    offset = 0
    
    # After opening clause patterns
    clause_patterns = [
        'In practice', 'That said', 'Which means', 'And that means',
        'So when', 'But when', 'Even though', 'Given that'
    ]
    
    for pattern in clause_patterns:
        matches = list(re.finditer(re.escape(pattern), text))
        for match in matches:
            pos = match.end() + offset
            text = text[:match.end()] + ZWSP + text[match.end():]
            offset += len(ZWSP)
            perturbations.append({
                "type": "zwsp_after_clause_pattern",
                "position": pos,
                "character": ZWSP,
                "context": pattern
            })

    # Before long noun phrases (after 'the')
    def replace_the(match):
        nonlocal offset
        pos = match.start() + len('the ') + offset
        offset += len(ZWSP)
        perturbations.append({
            "type": "zwsp_before_noun_phrase",
            "position": pos,
            "character": ZWSP,
            "context": "the " + match.group(1)
        })
        return f"the {ZWSP}{match.group(1)}"
    
    text = re.sub(r'\bthe ([a-z])', replace_the, text)

    # Mid-sentence after semicolons
    def replace_semicolon(match):
        nonlocal offset
        pos = match.start() + 1 + offset
        offset += len(ZWSP)
        perturbations.append({
            "type": "zwsp_after_semicolon",
            "position": pos,
            "character": ZWSP,
            "context": ";"
        })
        return ';' + ZWSP + match.group(1)
    
    text = re.sub(r';(\s)', replace_semicolon, text)

    return text, perturbations


def apply_line_break_trick(text: str) -> str:
    """Full pipeline for the line break bypass trick."""
    text, _ = fragment_sentences(text)
    text, _ = inject_invisible_breaks(text)
    return text


def apply_line_break_trick_with_metadata(text: str) -> Dict:
    """
    Apply Stage 5 transformations with full instrumentation.
    
    Returns:
        Dictionary containing:
        - output: transformed text
        - zwsp_count: number of ZWSP characters inserted
        - shy_count: number of SHY characters inserted
        - total_insertions: total perturbations
        - input_length: original character count
        - output_length: final character count
        - utf8_valid: whether output is valid UTF-8
        - perturbations: detailed list of all insertions
        - success: whether operation succeeded
        - error: error message if failed
    """
    result = {
        "output": text,
        "zwsp_count": 0,
        "shy_count": 0,
        "total_insertions": 0,
        "input_length": len(text) if text else 0,
        "output_length": 0,
        "utf8_valid": True,
        "perturbations": [],
        "success": False,
        "error": None
    }
    
    try:
        if not text:
            result["output_length"] = 0
            result["success"] = True
            return result
        
        # Apply fragment_sentences
        text_after_fragment, fragment_perts = fragment_sentences(text)
        
        # Apply inject_invisible_breaks
        text_final, inject_perts = inject_invisible_breaks(text_after_fragment)
        
        # Combine perturbations
        all_perturbations = fragment_perts + inject_perts
        
        # Count character types
        zwsp_count = sum(1 for p in all_perturbations if p["character"] == ZWSP)
        shy_count = sum(1 for p in all_perturbations if p["character"] == SHY)
        
        # Validate UTF-8
        try:
            text_final.encode('utf-8').decode('utf-8')
            utf8_valid = True
        except (UnicodeEncodeError, UnicodeDecodeError):
            utf8_valid = False
        
        result.update({
            "output": text_final,
            "zwsp_count": zwsp_count,
            "shy_count": shy_count,
            "total_insertions": len(all_perturbations),
            "output_length": len(text_final),
            "utf8_valid": utf8_valid,
            "perturbations": all_perturbations,
            "success": True
        })
        
    except Exception as e:
        result["error"] = str(e)
        result["success"] = False
    
    return result
