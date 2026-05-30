"""
pipeline/turnitin_bypass.py
Stage 5 — Targets Turnitin and other sophisticated AI detectors.
Adds deliberate human imperfections, mixed formality, and natural inconsistencies.
"""

import httpx
import json
import logging
import re

logger = logging.getLogger(__name__)

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "llama3.2:latest"

SYSTEM_INSTRUCTION = """You are a human writing coach doing a final edit. Output ONLY the edited text.
STRICT RULES:
- Output ONLY the edited text. Nothing else.
- Do NOT add any commentary, notes, or explanations before or after.
- Do NOT say "Here is", "I've edited", "Note:", or anything like that.
- Do NOT refuse. Just edit."""

TURNITIN_PROMPT = """{system}

You are making this text look like it was genuinely written by a human student or professional.
Sophisticated AI detectors like Turnitin look for:
- Uniform sentence complexity (fix this by mixing simple and complex sentences)
- Perfect logical flow (fix this by adding slight tangents or hesitations)  
- Consistent formality (fix this by occasionally dropping to simpler language)
- No personal voice (fix this by adding opinion markers)

MAKE THESE SPECIFIC CHANGES:
1. Add 1-2 em dashes for asides: "this approach — while not perfect — works well"
2. Add 1-2 parenthetical comments: "(which is worth keeping in mind)" or "(and that matters)"
3. Add personal opinion markers: "I'd argue", "in my view", "to be honest", "frankly"
4. Create ONE very short paragraph (1 sentence only) somewhere in the middle
5. Mix vocabulary complexity — use one very simple word where a complex one would be expected
6. Add ONE natural comma splice (two independent clauses joined with just a comma)
7. Vary paragraph lengths: make sure no two consecutive paragraphs are the same length
8. Keep ALL the meaning exactly the same — just change the style

INPUT TEXT:
{text}

EDITED TEXT:"""


def clean_output(text: str) -> str:
    text = text.strip()
    for phrase in ["Here is", "Here's", "I've", "I have", "Note:", "Edited:", "Sure,", "Certainly,"]:
        if text.startswith(phrase):
            newline_idx = text.find("\n")
            if newline_idx != -1:
                text = text[newline_idx:].strip()
    lines = text.split("\n")
    clean_lines = []
    for line in lines:
        stripped = line.strip()
        if any(stripped.startswith(p) for p in ["Note:", "(Note", "I've", "I have", "I kept", "I removed", "I made"]):
            break
        clean_lines.append(line)
    result = "\n".join(clean_lines).strip()
    result = re.sub(r'\s*\(Note:.*?\)\s*$', '', result, flags=re.DOTALL).strip()
    return result if result else text


async def turnitin_bypass(text: str) -> str:
    """Stage 5 — Add human imperfections to fool Turnitin and similar detectors."""
    prompt = TURNITIN_PROMPT.format(system=SYSTEM_INSTRUCTION, text=text)
    payload = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "stream": True,
        "options": {
            "temperature": 0.88,
            "top_p": 0.94,
            "top_k": 60,
            "repeat_penalty": 1.15,
            "num_predict": 1200
        }
    }
    try:
        async with httpx.AsyncClient(timeout=None) as client:
            result_text = ""
            async with client.stream("POST", OLLAMA_URL, json=payload) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if line.strip():
                        chunk = json.loads(line)
                        result_text += chunk.get("response", "")
                        if chunk.get("done", False):
                            break
        return clean_output(result_text) if result_text.strip() else text
    except Exception as e:
        logger.warning(f"Turnitin bypass failed, returning original. Error: {e}")
        return text
