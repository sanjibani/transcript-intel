"""
LLM client wrapper for the transcript-intel pipeline.

What this does:
    Provides a single function `llm_call(prompt, system=...)` that calls an
    OpenAI-compatible chat completion API. Defaults to MiniMax but works
    with any OpenAI-compatible endpoint via env vars.

Configuration via env vars (loaded from .env file if present):
    LLM_BASE_URL  - API endpoint (default: https://api.minimax.chat/v1)
    LLM_API_KEY   - your API key (REQUIRED)
    LLM_MODEL     - model name (default: MiniMax-Text-01)

Setup:
    1. Copy .env.example to .env:   cp .env.example .env
    2. Edit .env and put your real API key there
    3. Run the pipeline — it will read from .env automatically

Safety:
    .env is gitignored. NEVER commit it. The pipeline will refuse to log
    the API key even if the env var is set.

Graceful degradation:
    If LLM_API_KEY is not set, llm_call() returns None and logs a warning.
    Pipeline stages that depend on LLM should check for None and fall back
    to rules-only mode.

Cost control:
    Default temperature=0.0 for reproducibility.
    Token limit set to 1000 (most prompts need <500).
"""

from __future__ import annotations

import logging
import os
import sys
from pathlib import Path
from typing import Optional

# Load .env file if it exists (silently skip if not)
try:
    from dotenv import load_dotenv
    _env_path = Path(__file__).resolve().parent.parent / ".env"
    if _env_path.exists():
        load_dotenv(_env_path, override=False)  # don't override existing env vars
except ImportError:
    pass  # python-dotenv not installed; rely on real env vars

logger = logging.getLogger(__name__)

# Safety: never log the actual API key, even in debug mode
def _safe_key_for_log() -> str:
    key = os.environ.get("LLM_API_KEY") or os.environ.get("OPENAI_API_KEY") or os.environ.get("MINIMAX_API_KEY")
    if not key:
        return "<not set>"
    if len(key) < 8:
        return "<too short to log>"
    return f"{key[:4]}...{key[-4:]}  ({len(key)} chars)"


def _get_client():
    """Build an OpenAI client configured from env vars.

    Returns None if API key is missing.
    """
    api_key = os.environ.get("LLM_API_KEY") or os.environ.get("OPENAI_API_KEY") or os.environ.get("MINIMAX_API_KEY")
    if not api_key:
        return None

    try:
        from openai import OpenAI
    except ImportError:
        logger.warning("openai library not installed; LLM calls unavailable")
        return None

    base_url = os.environ.get("LLM_BASE_URL", "https://api.minimax.chat/v1")
    logger.debug(f"LLM client: base_url={base_url}, model={os.environ.get('LLM_MODEL', 'MiniMax-Text-01')}, key={_safe_key_for_log()}")
    return OpenAI(api_key=api_key, base_url=base_url)


def llm_call(prompt: str, system: str = "", model: Optional[str] = None,
             temperature: float = 0.0, max_tokens: int = 1000) -> Optional[str]:
    """Call the LLM. Returns the response text, or None if unavailable.

    Args:
        prompt: The user message.
        system: Optional system prompt.
        model: Override the default model.
        temperature: 0.0 for reproducibility.
        max_tokens: Cap on response length.

    Returns:
        Response text, or None if LLM is not configured / call failed.
    """
    client = _get_client()
    if client is None:
        logger.debug("LLM not configured; skipping call")
        return None

    model_name = model or os.environ.get("LLM_MODEL", "MiniMax-Text-01")

    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    try:
        response = client.chat.completions.create(
            model=model_name,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return response.choices[0].message.content
    except Exception as exc:  # noqa: BLE001
        logger.warning(f"LLM call failed: {exc}")
        return None


def llm_available() -> bool:
    """Check whether LLM is configured and reachable."""
    return _get_client() is not None


if __name__ == "__main__":
    # Quick smoke test
    print(f"LLM key status: {_safe_key_for_log()}")
    print(f"LLM base URL:   {os.environ.get('LLM_BASE_URL', 'https://api.minimax.chat/v1')}")
    print(f"LLM model:      {os.environ.get('LLM_MODEL', 'MiniMax-Text-01')}")
    if llm_available():
        result = llm_call("Reply with just the word 'OK' and nothing else.")
        print(f"\nLLM response: {result!r}")
    else:
        print("\nLLM not configured.")
        print("Setup: cp .env.example .env, then edit .env with your real key.")
        sys.exit(0)