import httpx
import json
import logging

logger = logging.getLogger(__name__)

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "llama3.2:latest"

TONE_PROMPTS = {
    "btech_student": "Rewrite as a real BTech student writing a report. Keep it natural, clear, and direct. Use a simple student voice. Preserve the meaning.",
    "storytelling": "Rewrite as a human storyteller. Make it warm, direct, and personal. Keep the meaning the same.",
    "formal_report": "Rewrite for a formal report. Keep it professional, clear, and readable. Preserve the meaning and structure as much as possible.",
    "academic": "Rewrite for an academic paper. Keep the tone measured, precise, and clear. Preserve the meaning.",
    "casual": "Rewrite casually like texting a smart friend. Keep it natural and easy to read. Preserve the meaning.",
    "formal_professional": "Rewrite for a professional business memo. Keep it sharp, clear, and direct. Preserve the meaning.",
    "conversational": "Rewrite as a blog post by a real person. Keep it natural, conversational, and easy to follow. Preserve the meaning.",
    "technical": "Rewrite as technical documentation by a real engineer. Keep it precise, direct, and clear. Preserve the meaning.",
    "creative": "Rewrite creatively with personality and rhythm. Keep it natural while preserving the meaning.",
}

AGGRESSIVENESS_INSTRUCTIONS = {
    1: "Make light edits only. Improve wording and clarity while staying very close to the original.",
    2: "Moderately rewrite. Improve flow, sentence variety, and readability while preserving meaning.",
    3: "Heavily rewrite. Improve structure and flow more noticeably while keeping all facts and meaning intact."
}

SYSTEM_INSTRUCTION = """You are a text rewriter.
Your only job is to output the rewritten text.

STRICT RULES:
- Output only the rewritten text.
- Do not add commentary, bullet points, or explanations.
- Do not add headings unless they already exist in the input.
- Preserve the meaning.
- Keep the tone consistent with the selected style.
- Improve clarity, flow, and readability.
- Avoid repetition.
- Do not introduce new facts or opinions.
"""

async def rewrite_chunk(text: str, tone: str, aggressiveness: int, client: httpx.AsyncClient) -> str:
    tone_instruction = TONE_PROMPTS.get(tone, TONE_PROMPTS["formal_report"])
    aggr_instruction = AGGRESSIVENESS_INSTRUCTIONS.get(aggressiveness, AGGRESSIVENESS_INSTRUCTIONS[2])

    prompt = f"""{SYSTEM_INSTRUCTION}

Style:
{tone_instruction}

Editing level:
{aggr_instruction}

INPUT TEXT:
{text}

REWRITTEN TEXT:"""

    temperature = 0.75 + (aggressiveness * 0.05)

    payload = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "stream": True,
        "options": {
            "temperature": min(temperature, 0.95),
            "top_p": 0.92,
            "top_k": 50,
            "repeat_penalty": 1.15,
            "num_predict": 1024
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
        for prefix in ["Here is", "Here's", "I've", "I have", "Note:", "Rewritten:", "Output:"]:
            if cleaned.startswith(prefix):
                newline_idx = cleaned.find("\n")
                if newline_idx != -1:
                    cleaned = cleaned[newline_idx:].strip()

        return cleaned if cleaned else text

    except Exception as e:
        logger.warning(f"LLM rewrite failed, returning original. Error: {e}")
        return text


async def style_rewrite(merged_units: list[str], tone: str, aggressiveness: int) -> list[str]:
    rewritten = []
    async with httpx.AsyncClient(timeout=None) as client:
        for unit in merged_units:
            if not unit.strip():
                rewritten.append("")
                continue
            result = await rewrite_chunk(unit, tone, aggressiveness, client)
            rewritten.append(result)
    return rewritten
