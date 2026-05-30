"""
pipeline/flow_smoother.py
"""

import httpx
import json
import logging

logger = logging.getLogger(__name__)

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "llama3.2:latest"

SYSTEM_INSTRUCTION = """You are a text editor. Your ONLY job is to output the improved text.
STRICT RULES:
- Output ONLY the improved text. Nothing else.
- Do NOT write anything before the improved text.
- Do NOT write anything after the improved text.
- Do NOT say "Here is", "I've edited", "Note:", "I cannot", or any other commentary.
- Do NOT refuse. Just improve the text.
- Do NOT add bullet points or lists."""

FLOW_PROMPT = """{system}

EDITING INSTRUCTIONS:
1. Remove ALL AI phrases: "furthermore", "subsequently", "it is worth noting", "it is imperative", "in conclusion", "it can be observed", "additionally", "moreover", "it is important to note", "notably", "delve", "tapestry", "nuanced"
2. Replace with human phrases: "so", "which means", "and", "but", "because of this", "that's why", "in practice", "that said", "turns out", "honestly"
3. Vary sentence lengths: after two long sentences add one short one (under 8 words)
4. Add contractions: "it's", "that's", "don't", "can't", "we've", "isn't", "doesn't"
5. Start 1-2 sentences with "And", "But", or "So"
6. Keep meaning exactly the same

INPUT TEXT:
{text}

IMPROVED TEXT:"""


def split_into_paragraphs(text: str) -> list[str]:
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    return paragraphs if paragraphs else [text]


async def smooth_chunk(text: str, client: httpx.AsyncClient) -> str:
    prompt = FLOW_PROMPT.format(system=SYSTEM_INSTRUCTION, text=text)
    payload = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "stream": True,
        "options": {
            "temperature": 0.82,
            "top_p": 0.93,
            "top_k": 50,
            "repeat_penalty": 1.2,
            "num_predict": 900
        }
    }
    try:
        result_text = ""
        async with client.stream("POST", OLLAMA_URL, json=payload) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                if line.strip():
                    chunk = json.loads(line)
                    result_text += chunk.get("response", "")
                    if chunk.get("done", False):
                        break

        # Strip accidental preamble
        cleaned = result_text.strip()
        for prefix in ["Here is", "Here's", "I've", "I have", "Note:", "Improved:", "Output:"]:
            if cleaned.startswith(prefix):
                newline_idx = cleaned.find("\n")
                if newline_idx != -1:
                    cleaned = cleaned[newline_idx:].strip()

        return cleaned if cleaned else text

    except Exception as e:
        logger.warning(f"Flow smooth failed, returning original. Error: {e}")
        return text


async def flow_smooth(text: str) -> str:
    paragraphs = split_into_paragraphs(text)
    smoothed_paragraphs = []

    async with httpx.AsyncClient(timeout=None) as client:
        for paragraph in paragraphs:
            result = await smooth_chunk(paragraph, client)
            smoothed_paragraphs.append(result)

    return "\n\n".join(smoothed_paragraphs)
