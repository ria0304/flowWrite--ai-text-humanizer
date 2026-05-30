"""
pipeline/style_rewriter.py
"""

import httpx
import json
import logging

logger = logging.getLogger(__name__)

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "llama3.2:latest"

TONE_PROMPTS = {
    "btech_student": "Rewrite as a real BTech student. Use 'we', 'our', 'basically', 'so', contractions. Mix short and long sentences. Start some with 'And', 'But', 'So'. No AI phrases like 'furthermore', 'additionally', 'it is worth noting'.",
    "storytelling": "Rewrite as a human storyteller. Warm, direct, personal. Use contractions. Mix sentence lengths. Start some with 'And', 'But', 'So'. No AI phrases.",
    "formal_report": "Rewrite for a formal report by a real human. Vary sentence lengths. Use 'in practice', 'that said', 'which means'. Occasional contractions. No AI phrases like 'furthermore', 'additionally', 'it is worth noting', 'it is imperative'.",
    "academic": "Rewrite for an academic paper by a real researcher. Use hedging: 'this suggests', 'it appears that'. Vary sentence lengths. Use 'that said', 'in practice'. No AI phrases like 'furthermore', 'additionally', 'it is worth noting'.",
    "casual": "Rewrite casually like talking to a friend. Use contractions everywhere. Short sentences. Add 'basically', 'the thing is', 'honestly'. Start sentences with 'And', 'But', 'So'. No AI phrases.",
    "formal_professional": "Rewrite for professional business context. Sharp and direct. Vary sentence lengths. Use 'in practice', 'that said'. No AI phrases like 'furthermore', 'additionally', 'it is worth noting'.",
    "conversational": "Rewrite as a blog post by a real person. Use contractions everywhere. Mix short and long sentences. Add 'here's the thing', 'honestly', 'what's interesting'. Start sentences with 'And', 'But', 'So'. No AI phrases.",
    "technical": "Rewrite as technical docs by a real engineer. Precise and direct. Active voice. Short sentences. Use 'in practice', 'under the hood'. No vague filler phrases.",
    "creative": "Rewrite creatively with personality. Vary sentence rhythm dramatically. No AI clichés: 'delve', 'tapestry', 'nuanced', 'furthermore'. Add human asides.",
}

AGGRESSIVENESS_INSTRUCTIONS = {
    1: "Make light changes only. Stay close to original wording.",
    2: "Moderately rewrite. Restructure sentences and add natural connectors.",
    3: "Heavily rewrite. Vary lengths dramatically. Add contractions and personal voice."
}

SYSTEM_INSTRUCTION = """You are a text rewriter. Your ONLY job is to output the rewritten text.
STRICT RULES:
- Output ONLY the rewritten text. Nothing else.
- Do NOT write anything before the rewritten text.
- Do NOT write anything after the rewritten text.
- Do NOT say "Here is", "I've rewritten", "Note:", "I cannot", or any other commentary.
- Do NOT refuse. Just rewrite.
- Do NOT add bullet points or lists."""


async def rewrite_chunk(text: str, tone: str, aggressiveness: int, client: httpx.AsyncClient) -> str:
    tone_instruction = TONE_PROMPTS.get(tone, TONE_PROMPTS["formal_report"])
    aggr_instruction = AGGRESSIVENESS_INSTRUCTIONS.get(aggressiveness, AGGRESSIVENESS_INSTRUCTIONS[2])

    prompt = f"""{SYSTEM_INSTRUCTION}

Style: {tone_instruction}
Intensity: {aggr_instruction}

INPUT TEXT:
{text}

REWRITTEN TEXT:"""

    temperature = 0.75 + (aggressiveness * 0.1)

    payload = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "stream": True,
        "options": {
            "temperature": min(temperature, 1.0),
            "top_p": 0.92,
            "top_k": 50,
            "repeat_penalty": 1.2,
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

        # Strip any accidental preamble the model adds
        cleaned = result_text.strip()
        for prefix in ["Here is", "Here's", "I've", "I have", "Note:", "Rewritten:", "Output:"]:
            if cleaned.startswith(prefix):
                # Find the first newline and skip the preamble line
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
