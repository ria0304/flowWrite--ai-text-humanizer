import httpx
import json
import logging

logger = logging.getLogger(__name__)

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "llama3.2:latest"

SYSTEM_INSTRUCTION = """You are a text editor. Output ONLY the edited text.
STRICT RULES:
- Output ONLY the edited text. Nothing else.
- Do NOT add commentary, explanations, or bullet points.
- Do NOT say "Here is", "I've edited", "Note:", or anything similar.
- Preserve the meaning exactly.
- Do NOT make the text more formal or complex.
- Do NOT replace simple words with longer ones.
- Do NOT add words like: significant, crucial, fundamental, leverage, implement, facilitate.
"""

FLOW_PROMPT = """{system}

EDITING INSTRUCTIONS:
1. Fix awkward phrasing and improve flow — but keep words simple.
2. Target Flesch Reading Ease of 60-70 (conversational, magazine level).
3. If any sentence is over 25 words, split it into two.
4. Replace long words with shorter ones wherever possible:
   - 'implementation' → 'use' or 'setup'
   - 'utilization' → 'use'
   - 'facilitate' → 'help'
   - 'significant' → 'big' or 'major'
   - 'leverage' → 'use'
   - 'demonstrate' → 'show'
   - 'consequently' → 'so'
   - 'nevertheless' → 'still' or 'but'
5. Keep sentence length varied — mix short (5-8 words) and medium (15-20 words).
6. Remove repeated filler phrases.
7. Keep the tone exactly as it came in — do NOT make it more formal.
8. Do not add new ideas.

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
            "temperature": 0.75,
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
