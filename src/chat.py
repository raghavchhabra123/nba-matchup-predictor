"""Grounded matchup assistant (free — Groq-hosted Llama).

Not a document-RAG system: the "knowledge" is the model's own live output for
the current matchup, injected as FACTS. The assistant answers strictly from
those facts, so it can't misstate the numbers. Needs a free GROQ_API_KEY
(https://console.groq.com) in Streamlit secrets or the environment.
"""
from __future__ import annotations

MODEL = 'llama-3.1-8b-instant'

SYSTEM = (
    "You are the built-in assistant for an NBA Matchup Predictor app. You do two "
    "things: (1) explain the CURRENT matchup using the FACTS, and (2) explain "
    "basketball concepts, stats, and strategy using the KNOWLEDGE section when "
    "it's provided. Be concise and conversational (2–4 sentences, plain English, "
    "no betting jargon).\n"
    "- For matchup numbers, use ONLY the FACTS. Never invent a number — if it's "
    "not in the FACTS, say so.\n"
    "- If someone changes the scenario ('what if X sits?'), explain the direction "
    "and rough size, and suggest toggling it in the Players tab for the exact number.\n"
    "- For concept/strategy/stat questions, answer from the KNOWLEDGE section and "
    "mention the source in parentheses. If KNOWLEDGE is empty or doesn't cover it, "
    "give a brief general answer and say it's not from the app's sources.\n"
    "- Decline only if a question is unrelated to basketball."
)


def ask(question: str, facts: str, history: list[tuple[str, str]],
        api_key: str, model: str = MODEL) -> str:
    """Return the assistant's answer, grounded on `facts`. Raises on API error."""
    from groq import Groq
    client = Groq(api_key=api_key)
    messages = [{'role': 'system', 'content': f'{SYSTEM}\n\nFACTS:\n{facts}'}]
    for user_msg, bot_msg in history[-4:]:
        messages.append({'role': 'user', 'content': user_msg})
        messages.append({'role': 'assistant', 'content': bot_msg})
    messages.append({'role': 'user', 'content': question})
    resp = client.chat.completions.create(
        model=model, messages=messages, temperature=0.3, max_tokens=350)
    return resp.choices[0].message.content.strip()
