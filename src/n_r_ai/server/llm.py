from __future__ import annotations
import json
import os
from typing import Any, Dict, Optional
from openai import OpenAI

class LLMConfig:
    def __init__(self) -> None:
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.base_url = os.getenv("LLM_BASE_URL") or os.getenv("OPENAI_BASE_URL")
        self.model = os.getenv("LLM_MODEL", "gpt-4o-mini")
        self.temperature = float(os.getenv("LLM_TEMPERATURE", "0.7"))

    def is_configured(self) -> bool:
        return bool(self.api_key)

    def client(self) -> OpenAI:
        if not self.is_configured():
            raise RuntimeError("LLM not configured: set OPENAI_API_KEY and optionally LLM_BASE_URL, LLM_MODEL")
        return OpenAI(api_key=self.api_key, base_url=self.base_url) if self.base_url else OpenAI(api_key=self.api_key)


def llm_choose_action(
    state_summary: str,
    actions: list[dict[str, Any]],
    persona: str | None = None,
    temperature: float | None = None,
    config: Optional[LLMConfig] = None,
) -> dict[str, Any]:
    cfg = config or LLMConfig()
    if not cfg.is_configured():
        raise RuntimeError("LLM not configured: set OPENAI_API_KEY and optionally LLM_BASE_URL, LLM_MODEL")

    sys = (
        "You are an AI agent playing a board game. Think step by step and choose ONE action from the provided legal actions. "
        "Role-play the given persona, try to win logically, and return STRICT JSON only."
    )

    persona_text = persona.strip() if persona else ""

    user = (
        f"Persona: {persona_text or 'neutral'}\n"
        f"State:\n{state_summary}\n\n"
        "Legal actions are indexed starting at 0.\n"
        f"Actions: {json.dumps(actions, ensure_ascii=False)}\n\n"
        "Return JSON ONLY in the following schema (no extra text):\n"
        '{"pick": <int index>, "rationale": <short string>}'
    )

    client = cfg.client()

    completion = client.chat.completions.create(
        model=cfg.model,
        temperature=temperature if temperature is not None else cfg.temperature,
        messages=[
            {"role": "system", "content": sys},
            {"role": "user", "content": user},
        ],
        response_format={"type": "json_object"},
    )

    content = completion.choices[0].message.content or "{}"
    try:
        data = json.loads(content)
    except Exception:
        # Best-effort extraction of JSON object
        start = content.find("{")
        end = content.rfind("}")
        if start != -1 and end != -1 and end > start:
            data = json.loads(content[start : end + 1])
        else:
            raise RuntimeError("LLM returned non-JSON content")

    if not isinstance(data.get("pick"), int):
        raise RuntimeError("LLM response missing integer 'pick'")

    idx = data["pick"]
    if idx < 0 or idx >= len(actions):
        raise RuntimeError("LLM pick out of range")

    rationale = data.get("rationale", "")
    return {"pick": idx, "rationale": rationale}
