"""Provider-agnostic LLM call helper.

OpenAI models go through the Responses API (as before). Models whose name
starts with "deepseek" are routed to DeepSeek's OpenAI-compatible Chat
Completions endpoint. Slash-qualified model names (for example,
``stealth/ox-alpha``) are routed through OpenRouter's Chat Completions API.

"""

from __future__ import annotations

import os

from openai import OpenAI

from info_marketplace.load_env import load_env

load_env()

DEEPSEEK_BASE_URL = "https://api.deepseek.com"
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

_clients: dict[str, OpenAI] = {}


def is_deepseek(model_name: str) -> bool:
    # Bare DeepSeek checkpoint names use the direct provider. Slash-qualified
    # IDs are OpenRouter namespace/model identifiers, including
    # ``deepseek/deepseek-v4-flash``.
    return "/" not in model_name and model_name.lower().startswith("deepseek")


def is_openrouter(model_name: str) -> bool:
    return "/" in model_name and not is_deepseek(model_name)


def model_provenance(model_name: str) -> dict[str, str]:
    """Return lightweight provider/checkpoint metadata for experiment logs."""
    if is_deepseek(model_name):
        return {"provider": "deepseek", "checkpoint": model_name, "revision": "api"}
    if is_openrouter(model_name):
        return {"provider": "openrouter", "checkpoint": model_name, "revision": "api"}
    return {"provider": "openai", "checkpoint": model_name, "revision": "api"}


def get_client(model_name: str, api_key: str | None = None) -> OpenAI:
    provider = "deepseek" if is_deepseek(model_name) else "openrouter" if is_openrouter(model_name) else "openai"
    if provider not in _clients:
        if provider == "deepseek":
            key = api_key or os.environ.get("DEEPSEEK_API_KEY")
            if not key:
                raise RuntimeError("DEEPSEEK_API_KEY is not set (put it in .env)")
            # Reasoner calls that hang were observed to wedge whole runs with
            # the default 600s timeout; fail fast and let the retry loop act.
            _clients[provider] = OpenAI(
                api_key=key, base_url=DEEPSEEK_BASE_URL, timeout=240.0, max_retries=1
            )
        elif provider == "openrouter":
            key = api_key or os.environ.get("OPENROUTER_API_KEY")
            if not key:
                raise RuntimeError("OPENROUTER_API_KEY is not set (put it in .env)")
            _clients[provider] = OpenAI(
                api_key=key, base_url=OPENROUTER_BASE_URL, timeout=240.0, max_retries=1
            )
        else:
            _clients[provider] = OpenAI(api_key=api_key or os.environ.get("OPENAI_API_KEY"))
    return _clients[provider]


def call_llm(
    model_name: str,
    instructions: str,
    input_text: str,
    reasoning_effort: str | None = None,
    max_output_tokens: int | None = None,
    api_key: str | None = None,
) -> str:
    """Single LLM call; returns the output text."""
    client = get_client(model_name, api_key)

    if is_deepseek(model_name):
        # Chat Completions; `reasoning` is unsupported (deepseek-reasoner
        # reasons implicitly), so reasoning_effort is ignored.
        kwargs = {}
        if max_output_tokens:
            kwargs["max_tokens"] = max_output_tokens
        if "reasoner" in model_name.lower():
            # deepseek-reasoner's hidden reasoning counts against max_tokens;
            # with game-length prompts, 3000 gets exhausted before any visible
            # content (finish_reason=length, empty content — verified live).
            kwargs["max_tokens"] = max(kwargs.get("max_tokens", 0), 32000)
        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": instructions},
                {"role": "user", "content": input_text},
            ],
            **kwargs,
        )
        return response.choices[0].message.content or ""

    if is_openrouter(model_name):
        # ox-alpha requires reasoning, but an unconstrained reasoning trace can
        # consume the entire completion budget before emitting the formatted
        # game action. Reserve room for visible output while retaining a
        # bounded private scratchpad.
        max_tokens = max(max_output_tokens or 0, 2048)
        extra_body = {}
        if reasoning_effort == "none":
            extra_body["reasoning"] = {"enabled": False}
        if model_name in {"stealth/ox-alpha", "z-ai/glm-5.3-flash"}:
            extra_body["reasoning"] = {"max_tokens": 1024}
        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": instructions},
                {"role": "user", "content": input_text},
            ],
            max_tokens=max_tokens,
            extra_body=extra_body or None,
        )
        return response.choices[0].message.content or ""

    kwargs = {}
    if reasoning_effort:
        kwargs["reasoning"] = {"effort": reasoning_effort}
    if max_output_tokens:
        kwargs["max_output_tokens"] = max_output_tokens
    response = client.responses.create(
        model=model_name,
        instructions=instructions,
        input=input_text,
        **kwargs,
    )
    return response.output_text
