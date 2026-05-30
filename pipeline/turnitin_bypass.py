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

You are making this text pass AI detectors by writing like a real human. Target these specific detector signals:

SENTENCE LENGTH — AI averages 29 words per sentence. Humans average 20-23.
→ Break any sentence over 25 words into two. Add some 5-8 word sentences.

FUNCTION WORDS — AI uses ~33% function words. Humans use ~40%.
→ Add more: the, it, is, was, are, were, this, that, these, those, they, their, there

PRONOUN SUBJECTS — AI uses noun subjects ("The implementation of X..."). Humans use pronouns.
→ Change "The implementation of AI presents challenges" to "It's not easy to implement AI"
→ Use "we", "it", "they", "you" to start sentences

BANNED WORDS — Replace every instance of: crucial, fundamental, significant, unprecedented,
multifaceted, leverage, delve, furthermore, additionally, it is worth noting, it is imperative,
Crucially, Fundamentally, Ultimately (as sentence starters)

EM DASH OVERUSE — Maximum 1 em dash in the entire text. Remove the rest.

REPETITIVE FILLER — "isn't it?", "to be honest", "that said" should appear MAX once each.
If they appear more, remove the duplicates.

KEEP:
- All the facts and meaning exactly the same
- The general tone and style
- Paragraph structure

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
            "temperature": 0.85,
            "top_p": 0.93,
            "top_k": 55,
            "repeat_penalty": 1.2,
            "num_predict": 1400
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
