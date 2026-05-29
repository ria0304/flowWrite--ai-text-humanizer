"""
pipeline/flow_smoother.py
"""

import httpx
import json
import logging

logger = logging.getLogger(__name__)

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "llama3.1:8b"

FLOW_PROMPT = """You are a human editor doing a final pass to make text completely undetectable by AI detectors like ZeroGPT.

Your job:
1. REMOVE every single AI phrase — zero tolerance:
   "it is worth noting", "furthermore", "subsequently", "it is imperative", "in conclusion",
   "it can be observed", "delve", "tapestry", "nuanced", "notably", "additionally", "moreover",
   "it is important to note", "in order to", "one must consider", "it should be noted"

2. REPLACE stiff transitions with human ones:
   Use: "so", "which means", "and", "but", "because of this", "that's why", "here's the thing",
   "in practice", "that said", "turns out", "honestly", "what's interesting"

3. VARY sentence lengths aggressively:
   - After two long sentences, add one very short one (under 8 words)
   - Break up sentences that are all the same length
   - Example rhythm: long. long. Short. long. Short. Short. long.

4. ADD human voice markers naturally:
   - Contractions: "it's", "that's", "don't", "can't", "we've", "isn't", "doesn't"
   - Occasional hedging: "in practice", "to be fair", "which is interesting"
   - Start 1-2 sentences with "And", "But", or "So"

5. Keep meaning exactly the same — do NOT add new information

6. Do NOT add bullet points
7. Do NOT add any intro or preamble — output the improved text only

Text:
{text}

Improved:"""


def split_into_paragraphs(text: str) -> list[str]:
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    return paragraphs if paragraphs else [text]


async def smooth_chunk(text: str, client: httpx.AsyncClient) -> str:
    prompt = FLOW_PROMPT.format(text=text)
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
        return result_text.strip() if result_text.strip() else text
    except Exception as e:
        logger.warning(f"Flow smooth failed, returning original. Error: {e}")
        return text


# FIX: Process EVERY paragraph — no skipping short ones
async def flow_smooth(text: str) -> str:
    paragraphs = split_into_paragraphs(text)
    smoothed_paragraphs = []

    async with httpx.AsyncClient(timeout=None) as client:
        for paragraph in paragraphs:
            result = await smooth_chunk(paragraph, client)
            smoothed_paragraphs.append(result)

    return "\n\n".join(smoothed_paragraphs)
