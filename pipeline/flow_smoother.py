import httpx
import json

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "mistral"

FLOW_PROMPT = """You are doing a final editing pass to make text sound more human and less AI-generated.

Your job:
- Remove any AI-sounding phrases: "it is worth noting", "furthermore", "subsequently", "it is imperative", "in conclusion", "it can be observed", "delve", "tapestry", "nuanced"
- Replace stiff transitions with natural ones: use "so", "which means", "and", "because of this", "that's why", "this is where"
- Make sure not all sentences are the same length — break up long ones, combine short choppy ones where it feels right
- If something sounds like it was written by a language model, rewrite that part to sound like a real person
- Keep the meaning exactly the same
- Do NOT add bullet points
- Do NOT add any intro or preamble — just output the improved text directly

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
            "temperature": 0.7,
            "top_p": 0.9,
            "repeat_penalty": 1.15,
            "num_predict": 800
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
        return result_text.strip()
    except Exception:
        return text  # fallback to original if anything goes wrong


async def flow_smooth(text: str) -> str:
    paragraphs = split_into_paragraphs(text)

    smoothed_paragraphs = []
    # timeout=None means wait as long as needed — no timeout ever
    async with httpx.AsyncClient(timeout=None) as client:
        for paragraph in paragraphs:
            if len(paragraph.split()) < 15:
                smoothed_paragraphs.append(paragraph)
            else:
                result = await smooth_chunk(paragraph, client)
                smoothed_paragraphs.append(result)

    return "\n\n".join(smoothed_paragraphs)
