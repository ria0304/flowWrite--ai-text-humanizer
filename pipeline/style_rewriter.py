import httpx
import json
import logging

logger = logging.getLogger(__name__)

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "llama3.2:latest"

TONE_PROMPTS = {
    "btech_student": "Rewrite as a real BTech student writing a report. Use 'we', 'our', 'basically', 'so', contractions. Mix short and long sentences. Start some with 'And', 'But', 'So'. Use pronouns like 'we found', 'we noticed'. NEVER use: 'furthermore', 'additionally', 'it is worth noting', 'crucial', 'fundamental', 'significant', 'ultimately', 'leverage', 'delve', 'multifaceted', 'unprecedented'.",
    "storytelling": "Rewrite as a human storyteller. Warm, direct, personal. Use contractions. Mix sentence lengths dramatically — some very short, some long. Start some with 'And', 'But', 'So'. NEVER use: 'furthermore', 'additionally', 'crucial', 'significant', 'unprecedented', 'multifaceted'.",
    "formal_report": "Rewrite for a formal report by a real human analyst. Vary sentence lengths — some under 10 words, some over 25. Use 'in practice', 'that said', 'which means'. Occasional contractions like 'it's', 'that's'. NEVER use: 'furthermore', 'additionally', 'it is worth noting', 'it is imperative', 'crucial', 'fundamental', 'leverage', 'multifaceted', 'unprecedented'.",
    "academic": "Rewrite for an academic paper by a real researcher. Use hedging: 'this suggests', 'it appears that', 'our results indicate'. Vary sentence lengths. Use 'that said', 'in practice'. Use first person plural 'we'. NEVER use: 'furthermore', 'additionally', 'it is worth noting', 'crucial', 'fundamental', 'unprecedented'.",
    "casual": "Rewrite casually like texting a smart friend. Use contractions everywhere. Short punchy sentences. Add 'basically', 'the thing is', 'honestly', 'look'. Start sentences with 'And', 'But', 'So'. NEVER use: 'furthermore', 'additionally', 'crucial', 'significant', 'unprecedented', 'multifaceted', 'leverage'.",
    "formal_professional": "Rewrite for a professional business memo. Sharp and direct. Vary sentence lengths. Use 'in practice', 'that said', 'the reality is'. NEVER use: 'furthermore', 'additionally', 'it is worth noting', 'crucial', 'leverage', 'multifaceted', 'unprecedented'.",
    "conversational": "Rewrite as a blog post by a real person. Use contractions everywhere. Mix short and long sentences. Add 'here's the thing', 'honestly', 'what's interesting is'. Start sentences with 'And', 'But', 'So'. Use 'I' and 'you'. NEVER use: 'furthermore', 'additionally', 'crucial', 'significant', 'unprecedented', 'multifaceted'.",
    "technical": "Rewrite as technical docs by a real engineer. Precise and direct. Active voice. Short sentences preferred. Use 'in practice', 'under the hood', 'the key thing here'. NEVER use vague filler or: 'furthermore', 'additionally', 'crucial', 'leverage', 'multifaceted'.",
    "creative": "Rewrite creatively with personality and rhythm. Vary sentence lengths dramatically. Add human asides and opinions. NEVER use: 'delve', 'tapestry', 'nuanced', 'furthermore', 'crucial', 'multifaceted', 'unprecedented', 'leverage'.",
}

AGGRESSIVENESS_INSTRUCTIONS = {
    1: "Make light changes only. Stay close to original wording but fix any AI phrases.",
    2: "Moderately rewrite. Restructure sentences, add natural connectors, vary lengths clearly.",
    3: "Heavily rewrite. Vary sentence lengths dramatically (some 5 words, some 30+). Add contractions, personal voice, and natural imperfections. Break up long formal sentences."
}

SYSTEM_INSTRUCTION = """You are a text rewriter. Your ONLY job is to output the rewritten text.
STRICT RULES:
- Output ONLY the rewritten text. Nothing else.
- Do NOT write anything before or after the rewritten text.
- Do NOT say "Here is", "I've rewritten", "Note:", "I cannot", or any commentary.
- Do NOT refuse. Just rewrite.
- Do NOT add bullet points or lists.
- TARGET Flesch Reading Ease score of 60-70 (conversational level).
- Use words under 3 syllables wherever possible.
- Replace long words with short ones: 'implementation' → 'use', 'utilization' → 'use', 'significant' → 'big', 'facilitate' → 'help', 'leverage' → 'use', 'demonstrate' → 'show', 'consequently' → 'so', 'nevertheless' → 'but'.
- Mix sentence lengths: some 5-8 words, some 20-25 words. Never 3 sentences the same length in a row.
- USE more pronouns (I, we, you, they) as sentence subjects instead of abstract nouns.
- AVOID starting 3 sentences in a row with the same structure."""


async def rewrite_chunk(text: str, tone: str, aggressiveness: int, client: httpx.AsyncClient) -> str:
    tone_instruction = TONE_PROMPTS.get(tone, TONE_PROMPTS["formal_report"])
    aggr_instruction = AGGRESSIVENESS_INSTRUCTIONS.get(aggressiveness, AGGRESSIVENESS_INSTRUCTIONS[2])

    prompt = f"""{SYSTEM_INSTRUCTION}

Style: {tone_instruction}
Intensity: {aggr_instruction}

INPUT TEXT:
{text}

REWRITTEN TEXT:"""

    temperature = 0.82 + (aggressiveness * 0.08)

    payload = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "stream": True,
        "options": {
            "temperature": min(temperature, 1.0),
            "top_p": 0.93,
            "top_k": 55,
            "repeat_penalty": 1.25,
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
