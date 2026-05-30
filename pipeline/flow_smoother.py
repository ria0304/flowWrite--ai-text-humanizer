import httpx
import json
import logging

logger = logging.getLogger(__name__)

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "llama3.2:latest"

SYSTEM_INSTRUCTION = """You are a text editor.
Your only job is to output the improved text.

STRICT RULES:
- Output only the improved text.
- Do not add commentary, explanations, or bullet points.
- Do not add headings unless they already exist in the input.
- Preserve the meaning.
- Improve clarity, flow, and readability.
- Keep the tone natural and consistent.
- Avoid repetition and awkward phrasing.
"""

FLOW_PROMPT = """{system}

EDITING INSTRUCTIONS:
1. Improve sentence flow and readability.
2. Remove repeated phrasing and unnecessary filler.
3. Keep the meaning exactly the same.
4. Preserve paragraph structure unless a small change improves clarity.
5. Make the text sound natural and smooth.
6. Do not add new ideas.

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
            "temperature": 0.65,
            "top_p": 0.92,
            "top_k": 50,
            "repeat_penalty": 1.15,
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
