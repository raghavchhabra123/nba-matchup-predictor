"""Grounded matchup assistant (free — Groq-hosted Llama).

Not a document-RAG system: the "knowledge" is the model's own live output for
the current matchup, injected as FACTS. The assistant answers strictly from
those facts, so it can't misstate the numbers. Needs a free GROQ_API_KEY
(https://console.groq.com) in Streamlit secrets or the environment.
"""
from __future__ import annotations

MODEL = 'llama-3.1-8b-instant'

SYSTEM = (
    "You are the built-in assistant for an NBA Matchup Predictor app. Answer "
    "ONLY using the FACTS provided about the current matchup and how the model "
    "works. Be concise and conversational (2–4 sentences, plain English, no "
    "betting jargon). Never invent numbers — if a number isn't in the FACTS, "
    "say so. If someone changes the scenario (e.g. 'what if X sits?'), explain "
    "the direction and roughly how much it moves things, and suggest toggling "
    "it in the Players tab for the exact number. If asked about anything "
    "outside this matchup or the model, say you can only help with this "
    "matchup and how the prediction is built."
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
