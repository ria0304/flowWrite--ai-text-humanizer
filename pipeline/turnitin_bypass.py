"""
pipeline/turnitin_bypass.py
Final polish stage for natural readability, clarity, and consistency.
Removes repetitive AI-like phrasing without targeting any detector.
"""
import httpx
import json
import logging
import re

logger = logging.getLogger(__name__)

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "llama3.2:latest"

SYSTEM_INSTRUCTION = """You are a human editor doing a final polish.
Output ONLY the edited text.

STRICT RULES:
- Output ONLY the edited text. Nothing else.
- Do NOT add commentary, notes, explanations, or bullet points.
- Do NOT say "Here is", "I've edited", "Note:", or similar phrases.
- Preserve the original meaning.
- Improve clarity, flow, and naturalness.
- Remove repetition and awkward phrasing.
- Vary sentence openings and sentence lengths when appropriate.
- Keep the tone consistent with the source text.
"""

POLISH_PROMPT = """{system}

EDITING INSTRUCTIONS:
1. Keep the facts and meaning the same.
2. Improve readability and flow.
3. Remove repetitive wording and filler.
4. Replace stiff or overly formal phrasing with natural wording.
5. Avoid repeated sentence openings.
6. Keep paragraph structure intact unless a small change improves flow.
7. Do not add new ideas or extra commentary.

INPUT TEXT:
{text}

POLISHED TEXT:"""


def clean_output(text: str) -> str:
    text = text.strip()

    for phrase in [
        "Here is", "Here's", "I've", "I have", "Note:",
        "Edited:", "Sure,", "Certainly,"
    ]:
        if text.startswith(phrase):
            newline_idx = text.find("\n")
            if newline_idx != -1:
                text = text[newline_idx:].strip()

    lines = text.split("\n")
    clean_lines = []

    for line in lines:
        stripped = line.strip()
        if any(stripped.startswith(p) for p in [
            "Note:", "(Note", "I've", "I have",
            "I kept", "I removed", "I made"
        ]):
            break
        clean_lines.append(line)

    result = "\n".join(clean_lines).strip()
    result = re.sub(r"\s*\(Note:.*?\)\s*$", "", result, flags=re.DOTALL).strip()
    return result if result else text


async def turnitin_bypass(text: str) -> str:
    """
    Final polish stage for natural readability.
    This stage is no longer detector-targeted.
    """
    prompt = POLISH_PROMPT.format(system=SYSTEM_INSTRUCTION, text=text)

    payload = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "stream": True,
        "options": {
            "temperature": 0.6,
            "top_p": 0.92,
            "top_k": 50,
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

        cleaned = clean_output(result_text)
        return cleaned if cleaned.strip() else text

    except Exception as e:
        logger.warning(f"Final polish failed, returning original. Error: {e}")
        return text
