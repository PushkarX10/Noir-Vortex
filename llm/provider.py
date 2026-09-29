"""
The Loop — Multi-Provider LLM Interface
High-performance, zero-dependency async LLM client supporting:
1. Google Gemini (via Gemini REST API)
2. OpenAI (GPT-4o, GPT-4o-mini, etc.)
3. Anthropic (Claude 3.5/3.7 Sonnet, Opus, Haiku)

Switchable via config or fallback automatically if one key is missing.
"""

import json
import logging
from typing import Optional, Any
import httpx

from config import LLMConfig

logger = logging.getLogger(__name__)

# Provider default models
PROVIDER_MODELS = {
    "google": "gemini-3.5-flash",
    "openai": "gpt-4o",
    "anthropic": "claude-3-7-sonnet-20250219",
}

PROVIDER_KEYS = {
    "google": "GOOGLE_API_KEY",
    "openai": "OPENAI_API_KEY",
    "anthropic": "ANTHROPIC_API_KEY",
}


def get_model_name(provider: Optional[str] = None) -> str:
    """Get the model identifier string for the given or configured provider."""
    prov = provider or LLMConfig.PROVIDER
    if LLMConfig.MODEL:
        return LLMConfig.MODEL
    return PROVIDER_MODELS.get(prov, PROVIDER_MODELS["openai"])


def _find_available_provider() -> str:
    """Fall through providers and return the first one with a valid key."""
    if LLMConfig.GOOGLE_API_KEY:
        return "google"
    if LLMConfig.OPENAI_API_KEY:
        return "openai"
    if LLMConfig.ANTHROPIC_API_KEY:
        return "anthropic"
    return LLMConfig.PROVIDER


def get_llm(
    provider: Optional[str] = None,
    temperature: float = 0.7,
    max_tokens: int = 4096,
) -> dict:
    """Get LLM configuration dictionary."""
    prov = provider or LLMConfig.PROVIDER
    key_var = PROVIDER_KEYS.get(prov, "")
    current_key = getattr(LLMConfig, key_var, "")

    if not current_key:
        available = _find_available_provider()
        if available != prov:
            logger.info(f"Provider '{prov}' has no key. Falling back to '{available}'.")
            prov = available

    model = get_model_name(prov)
    return {
        "provider": prov,
        "model": model,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }


async def _call_gemini(
    messages: list[dict],
    system_prompt: str,
    model: str,
    temperature: float,
    max_tokens: int,
    api_key: str,
) -> str:
    """Call Google Gemini REST API with automatic model fallback."""
    clean_model = model.replace("gemini/", "").replace("google/", "")
    models_to_try = [clean_model]
    for fallback in ("gemini-3.5-flash", "gemini-3-flash-preview", "gemini-flash-latest"):
        if fallback not in models_to_try:
            models_to_try.append(fallback)

    # Build Gemini content structure
    contents = []
    for m in messages:
        role = "user" if m.get("role") in ("user", "system") else "model"
        contents.append({
            "role": role,
            "parts": [{"text": m.get("content", "")}]
        })

    payload: dict[str, Any] = {
        "contents": contents,
        "generationConfig": {
            "temperature": temperature,
            "maxOutputTokens": max_tokens,
        }
    }

    if system_prompt:
        payload["systemInstruction"] = {
            "parts": [{"text": system_prompt}]
        }

    last_error = None
    async with httpx.AsyncClient(timeout=60.0) as client:
        for mod in models_to_try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{mod}:generateContent?key={api_key}"
            try:
                resp = await client.post(url, json=payload)
                resp.raise_for_status()
                data = resp.json()
                candidates = data.get("candidates", [])
                if candidates and "content" in candidates[0]:
                    parts = candidates[0]["content"].get("parts", [])
                    if parts:
                        return parts[0].get("text", "")
                return ""
            except httpx.HTTPStatusError as e:
                last_error = e
                logger.warning(f"Google Gemini model '{mod}' returned HTTP {e.response.status_code}. Trying next fallback...")
                continue
            except Exception as e:
                last_error = e
                logger.warning(f"Google Gemini model '{mod}' request failed: {e}. Trying next fallback...")
                continue

    if last_error:
        raise last_error
    return ""



async def _call_openai(
    messages: list[dict],
    system_prompt: str,
    model: str,
    temperature: float,
    max_tokens: int,
    api_key: str,
    response_format: Optional[dict] = None,
) -> str:
    """Call OpenAI Chat Completions REST API."""
    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    full_messages = []
    if system_prompt:
        full_messages.append({"role": "system", "content": system_prompt})
    full_messages.extend(messages)

    payload: dict[str, Any] = {
        "model": model,
        "messages": full_messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    if response_format:
        payload["response_format"] = response_format

    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(url, headers=headers, json=payload)
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"]


async def _call_anthropic(
    messages: list[dict],
    system_prompt: str,
    model: str,
    temperature: float,
    max_tokens: int,
    api_key: str,
) -> str:
    """Call Anthropic Messages REST API."""
    url = "https://api.anthropic.com/v1/messages"
    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "Content-Type": "application/json",
    }

    anthropic_messages = [
        {"role": "user" if m.get("role") != "assistant" else "assistant", "content": m.get("content", "")}
        for m in messages
    ]

    payload: dict[str, Any] = {
        "model": model,
        "messages": anthropic_messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    if system_prompt:
        payload["system"] = system_prompt

    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(url, headers=headers, json=payload)
        resp.raise_for_status()
        data = resp.json()
        return data["content"][0]["text"]


async def get_completion(
    messages: list[dict],
    system_prompt: str = "",
    provider: Optional[str] = None,
    temperature: float = 0.7,
    max_tokens: int = 4096,
    response_format: Optional[dict] = None,
) -> str:
    """
    Unified multi-provider completion caller.
    Executes via native REST endpoints with automatic provider fallback.
    """
    llm_info = get_llm(provider, temperature, max_tokens)
    prov = llm_info["provider"]
    model = llm_info["model"]

    # Try litellm if installed
    try:
        import litellm
        full_messages = []
        if system_prompt:
            full_messages.append({"role": "system", "content": system_prompt})
        full_messages.extend(messages)
        res = await litellm.acompletion(
            model=model,
            messages=full_messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return res.choices[0].message.content
    except (ImportError, Exception):
        pass

    # Direct native REST dispatch
    if prov == "google" and LLMConfig.GOOGLE_API_KEY:
        try:
            return await _call_gemini(messages, system_prompt, model, temperature, max_tokens, LLMConfig.GOOGLE_API_KEY)
        except Exception as e:
            logger.warning(f"Google Gemini call failed: {e}")

    if prov == "openai" and LLMConfig.OPENAI_API_KEY:
        try:
            return await _call_openai(messages, system_prompt, model, temperature, max_tokens, LLMConfig.OPENAI_API_KEY, response_format)
        except Exception as e:
            logger.warning(f"OpenAI call failed: {e}")

    if prov == "anthropic" and LLMConfig.ANTHROPIC_API_KEY:
        try:
            return await _call_anthropic(messages, system_prompt, model, temperature, max_tokens, LLMConfig.ANTHROPIC_API_KEY)
        except Exception as e:
            logger.warning(f"Anthropic call failed: {e}")

    # Fallback to any configured key
    if LLMConfig.GOOGLE_API_KEY:
        return await _call_gemini(messages, system_prompt, PROVIDER_MODELS["google"], temperature, max_tokens, LLMConfig.GOOGLE_API_KEY)
    elif LLMConfig.OPENAI_API_KEY:
        return await _call_openai(messages, system_prompt, PROVIDER_MODELS["openai"], temperature, max_tokens, LLMConfig.OPENAI_API_KEY, response_format)
    elif LLMConfig.ANTHROPIC_API_KEY:
        return await _call_anthropic(messages, system_prompt, PROVIDER_MODELS["anthropic"], temperature, max_tokens, LLMConfig.ANTHROPIC_API_KEY)

    raise ValueError(
        "No LLM API key configured. Please set GOOGLE_API_KEY, OPENAI_API_KEY, or ANTHROPIC_API_KEY in .env"
    )


def get_completion_sync(
    messages: list[dict],
    system_prompt: str = "",
    provider: Optional[str] = None,
    temperature: float = 0.7,
    max_tokens: int = 4096,
) -> str:
    """Synchronous completion helper."""
    import asyncio
    return asyncio.run(get_completion(messages, system_prompt, provider, temperature, max_tokens))
