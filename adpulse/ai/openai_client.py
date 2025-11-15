"""
LLM wrapper so the rest of the app can swap between OpenAI and local Ollama.
"""
from __future__ import annotations

import json
import os
from typing import Optional

import requests
from openai import OpenAI

_client: Optional[OpenAI] = None
_provider = os.getenv("ADPULSE_LLM_PROVIDER", "openai").lower()
_ollama_url = os.getenv("OLLAMA_API_URL", "http://127.0.0.1:11434/api/chat")
_ollama_model = os.getenv("OLLAMA_MODEL", "gpt-oss-20b")


def get_openai_client() -> OpenAI:
    global _client
    if _client is not None:
        return _client

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError(
            "Missing OPENAI_API_KEY environment variable. "
            "Set it before requesting AI insights or set ADPULSE_LLM_PROVIDER=ollama."
        )
    _client = OpenAI(api_key=api_key)
    return _client


def _generate_via_openai(prompt: str, max_tokens: int) -> str:
    client = get_openai_client()
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": "You are AdPulse, an elite performance marketing analyst.",
            },
            {"role": "user", "content": prompt},
        ],
        max_tokens=max_tokens,
        temperature=0.3,
    )
    if not response.choices:
        return "No response generated."
    return response.choices[0].message.content or "No response generated."


def _generate_via_ollama(prompt: str) -> str:
    payload = {
        "model": _ollama_model,
        "messages": [
            {"role": "system", "content": "You are AdPulse, an elite performance marketing analyst."},
            {"role": "user", "content": prompt},
        ],
        "stream": False,
    }
    try:
        response = requests.post(_ollama_url, json=payload, timeout=120)
        response.raise_for_status()
        data = response.json()
    except requests.RequestException as exc:
        raise RuntimeError(f"Ollama request failed: {exc}") from exc

    # Ollama chat endpoint returns {'message': {'content': ...}} or completions array depending on version
    if "message" in data:
        return data["message"].get("content", "No response generated.")
    if "messages" in data and data["messages"]:
        return data["messages"][-1].get("content", "No response generated.")
    if "response" in data:
        return data["response"]
    return json.dumps(data)


def generate_completion(prompt: str, max_tokens: int = 400) -> str:
    if _provider == "ollama":
        return _generate_via_ollama(prompt)
    return _generate_via_openai(prompt, max_tokens=max_tokens)
