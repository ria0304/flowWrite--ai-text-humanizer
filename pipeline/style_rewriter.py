"""
pipeline/style_rewriter.py
"""

import httpx
import json
import logging

logger = logging.getLogger(__name__)

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "mistral"

TONE_PROMPTS = {
    "btech_student": """Rewrite the text below so it sounds like a real BTech student wrote it.

Rules:
- Write like a real student — casual, direct, sometimes imperfect
- Use "we", "our", "basically", "so", "turns out", "which is why"
- Mix sentence lengths aggressively — some one-liners, some longer
- Add personal observations: "what's interesting is", "we noticed that", "honestly"
- Start some sentences with "And", "But", "So" — students do this naturally
- Remove ALL of these: "furthermore", "subsequently", "it is worth noting", "it can be observed", "in conclusion", "it is imperative", "additionally", "moreover"
- Use contractions: "it's", "we've", "don't", "that's", "isn't"
- Do NOT use bullet points
- Do NOT add any intro — just write it directly""",

    "storytelling": """Rewrite the text below so it sounds like a real person telling a story.

Rules:
- Write like a human narrator — warm, direct, with personality
- Use contractions: "it's", "we've", "don't", "that's", "wasn't"
- Mix sentence lengths — short dramatic ones, longer flowing ones
- Add personal voice: "what surprised us", "turns out", "honestly", "which is why"
- Start some sentences with "And", "But", "So" — storytellers do this
- Remove ALL: "furthermore", "subsequently", "it is worth noting", "additionally", "moreover"
- Sound like a real person who lived through this
- Do NOT use bullet points
- Do NOT add any intro — just write it directly""",

    "formal_report": """Rewrite the text below for a formal report written by a real thoughtful human — NOT AI.

Rules:
- Vary sentence length dramatically — one short sentence after two long ones creates human rhythm
- Add occasional hedging: "in practice", "to be fair", "that said", "this is worth considering"
- Use contractions sparingly but naturally: "it's", "that's", "doesn't"
- Remove ALL of: "furthermore", "subsequently", "it is worth noting", "it can be observed", "in conclusion", "it is imperative", "additionally", "moreover", "it is important to note"
- Replace with: "in practice", "that said", "which means", "so", "this is why", "as a result"
- Occasionally start a sentence with "And" or "But" — formal human writers do this
- Sound like a senior analyst wrote this on a deadline — sharp, direct, no fluff
- Do NOT use bullet points
- Do NOT add any intro — just write it directly""",

    "academic": """Rewrite the text below for an academic paper written by a real researcher — NOT AI.

Rules:
- Use academic vocabulary but avoid all AI clichés
- Remove ALL of: "furthermore", "subsequently", "it is worth noting", "it can be observed", "delve", "tapestry", "nuanced", "it is imperative", "additionally", "moreover"
- Add natural academic hedging: "this suggests", "one possible explanation", "it appears that", "the data points to"
- Vary sentence length — short sentences for emphasis after long analytical ones
- Occasionally use informal bridging: "that said", "in practice", "put simply"
- Sound like a PhD student writing under pressure — intelligent but human
- Do NOT use bullet points
- Do NOT add any intro — just write it directly""",

    "casual": """Rewrite the text below so it sounds like a real person casually explaining something.

Rules:
- Write like you're talking to a smart friend — relaxed, direct, real
- Use contractions everywhere: "it's", "we've", "don't", "can't", "that's", "isn't"
- Short sentences are great. Use them a lot.
- Add filler-like phrases humans use: "basically", "the thing is", "honestly", "I mean", "which is kind of wild"
- Remove ALL of: "furthermore", "subsequently", "it is worth noting", "additionally", "moreover"
- Start sentences with "And", "But", "So" — this is natural
- Sound genuinely human — imperfect rhythm makes it real
- Do NOT use bullet points
- Do NOT add any intro — just write it directly""",

    "formal_professional": """Rewrite the text below for a professional business context written by a real human.

Rules:
- Be sharp and direct — no vague filler
- Remove ALL of: "it is worth noting", "furthermore", "subsequently", "it is imperative", "in conclusion", "additionally", "moreover"
- Use concrete language — say exactly what something does or what happened
- Vary sentence length — short punchy sentences after longer explanations
- Add occasional real-person phrases: "in practice", "that said", "to be direct"
- Sound like a competent professional who writes quickly and clearly
- Do NOT use bullet points
- Do NOT add any intro — just write it directly""",

    "conversational": """Rewrite the text below as a blog post written by a real enthusiastic human.

Rules:
- Write like you genuinely care about this topic
- Use contractions everywhere: "it's", "we've", "you'll", "that's", "isn't", "don't"
- Mix short punchy sentences with longer flowing ones
- Add personal voice: "here's the thing", "what's interesting", "honestly", "that's actually why"
- Remove ALL: "furthermore", "subsequently", "it is worth noting", "additionally", "moreover"
- Start sentences with "And", "But", "So", "Here's" — bloggers do this
- Sound warm, real, and slightly informal
- Do NOT use bullet points
- Do NOT add any intro — just write it directly""",

    "technical": """Rewrite the text below as technical documentation written by a real engineer.

Rules:
- Be precise — say exactly what something does
- Remove ALL vague filler: "it is important to note", "it can be observed", "in order to", "it is worth noting"
- Use active voice: "the system fetches..." not "the fetching of data is performed by..."
- Keep sentences short and scannable — engineers skim
- Add occasional dev-voice phrases: "in practice", "under the hood", "which means", "so basically"
- Start some sentences with "And" or "But" — engineers write like this
- Sound like a developer writing for other developers
- Do NOT use bullet points
- Do NOT add any intro — just write it directly""",

    "creative": """Rewrite the text below in a creative, expressive way that sounds like a real human writer.

Rules:
- Use vivid but natural language — not over-the-top
- Vary sentence rhythm dramatically — short punchy ones, then longer flowing ones
- Avoid ALL AI clichés: "delve", "it is worth noting", "furthermore", "tapestry", "nuanced", "moreover"
- Write with personality — let your voice show
- Add human asides: "which is fascinating", "honestly", "and that matters"
- Imperfect rhythm is good — it sounds more real
- Do NOT use bullet points
- Do NOT add any intro — just write it directly""",
}

AGGRESSIVENESS_INSTRUCTIONS = {
    1: "Make light changes — fix flow and awkward phrasing but stay close to the original wording. Keep most sentences intact.",
    2: "Moderately rewrite — restructure sentences, improve naturalness, add human-sounding connectors and occasional contractions.",
    3: "Heavily rewrite — significantly rephrase everything. Vary sentence lengths dramatically. Add personal voice, contractions, and natural human hesitations. Make it sound like a real person wrote this from scratch while keeping the core meaning."
}


async def rewrite_chunk(text: str, tone: str, aggressiveness: int, client: httpx.AsyncClient) -> str:
    tone_prompt = TONE_PROMPTS.get(tone, TONE_PROMPTS["formal_report"])
    aggr_instruction = AGGRESSIVENESS_INSTRUCTIONS.get(aggressiveness, AGGRESSIVENESS_INSTRUCTIONS[2])

    prompt = f"""{tone_prompt}

Aggressiveness level: {aggr_instruction}

Text to rewrite:
{text}

Rewritten:"""

    # Higher temperature for aggressiveness=3 to maximize unpredictability
    temperature = 0.75 + (aggressiveness * 0.1)  # 0.85, 0.95, 1.05

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
        return result_text.strip() if result_text.strip() else text

    except Exception as e:
        logger.warning(f"LLM rewrite failed for chunk, returning original. Error: {e}")
        return text


async def style_rewrite(merged_units: list[str], tone: str, aggressiveness: int) -> list[str]:
    batch_size = 3
    rewritten = []

    async with httpx.AsyncClient(timeout=None) as client:
        for i in range(0, len(merged_units), batch_size):
            batch = merged_units[i:i + batch_size]
            combined = "\n".join(batch)
            result = await rewrite_chunk(combined, tone, aggressiveness, client)
            rewritten.append(result)

    return rewritten
