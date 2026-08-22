"""Provider-agnostic LLM call helper.

OpenAI models go through the Responses API (as before). Models whose name
starts with "deepseek" are routed to DeepSeek's OpenAI-compatible Chat
Completions endpoint (https://api.deepseek.com) using DEEPSEEK_API_KEY,
since DeepSeek does not implement the Responses API or the `reasoning`
parameter.
"""

from __future__ import annotations

import os

from openai import OpenAI

from info_marketplace.load_env import load_env

load_env()

DEEPSEEK_BASE_URL = "https://api.deepseek.com"

_clients: dict[str, OpenAI] = {}


def is_deepseek(model_name: str) -> bool:
    return model_name.lower().startswith("deepseek")


def get_client(model_name: str, api_key: str | None = None) -> OpenAI:
    provider = "deepseek" if is_deepseek(model_name) else "openai"
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
        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": instructions},
                {"role": "user", "content": input_text},
            ],
            **kwargs,
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
