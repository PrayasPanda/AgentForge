"""
Unified LLM client — supports Anthropic Claude and Ollama (local or cloud).

Configure via environment variables:

  # Choose provider (default: anthropic)
  LLM_PROVIDER=anthropic   # or: ollama

  # Anthropic
  ANTHROPIC_API_KEY=sk-ant-...

  # Ollama — LOCAL (no API key needed)
  OLLAMA_BASE_URL=http://localhost:11434/v1
  OLLAMA_MODEL=llama3.2

  # Ollama — CLOUD (real API key required)
  OLLAMA_BASE_URL=https://your-cloud-host/v1
  OLLAMA_MODEL=llama3.2
  OLLAMA_API_KEY=your-real-cloud-api-key

All public callers use the single `complete()` function — the provider
is transparent to the rest of the codebase.
"""

import os
from dotenv import load_dotenv

load_dotenv()

PROVIDER = os.getenv("LLM_PROVIDER", "anthropic").lower()

_ANTHROPIC_MODELS = {
    "default": "claude-sonnet-4-6",
    "fast": "claude-haiku-4-5-20251001",
}

_LOCAL_HOSTS = ("localhost", "127.0.0.1", "::1")


def _is_ollama_local(base_url: str = None) -> bool:
    url = base_url or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1")
    return any(h in url for h in _LOCAL_HOSTS)


def complete(prompt: str, max_tokens: int = 4096, fast: bool = False) -> str:
    """
    Send a prompt to the configured LLM and return the response text.

    Args:
        prompt: The user message.
        max_tokens: Maximum response tokens.
        fast: Use a smaller/faster model (Haiku for Anthropic; same model for Ollama).

    Returns:
        Response text as a plain string.
    """
    if PROVIDER == "ollama":
        return _ollama_complete(prompt, max_tokens)
    return _anthropic_complete(prompt, max_tokens, fast)


def provider_label() -> str:
    """Human-readable description of the active provider (for CLI output)."""
    if PROVIDER == "ollama":
        model = os.getenv("OLLAMA_MODEL", "llama3.2")
        base = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1")
        host = base.replace("/v1", "").rstrip("/")
        mode = "local" if _is_ollama_local() else "cloud"
        return f"Ollama {mode} ({model} @ {host})"
    return f"Anthropic ({_ANTHROPIC_MODELS['default']})"


# ── Anthropic ────────────────────────────────────────────────────────────────

def _anthropic_complete(prompt: str, max_tokens: int, fast: bool) -> str:
    import anthropic as _anthropic

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise EnvironmentError(
            "ANTHROPIC_API_KEY not set. "
            "Copy .env.example to .env and add your key, "
            "or set LLM_PROVIDER=ollama to use Ollama instead."
        )

    client = _anthropic.Anthropic(api_key=api_key)
    model = _ANTHROPIC_MODELS["fast"] if fast else _ANTHROPIC_MODELS["default"]

    message = client.messages.create(
        model=model,
        max_tokens=max_tokens,
        messages=[{"role": "user", "content": prompt}],
    )
    return message.content[0].text


# ── Ollama ────────────────────────────────────────────────────────────────────

def _ollama_complete(prompt: str, max_tokens: int) -> str:
    from openai import OpenAI

    base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1")
    model = os.getenv("OLLAMA_MODEL", "llama3.2")

    if _is_ollama_local():
        # Local Ollama doesn't need a real key — use placeholder
        api_key = os.getenv("OLLAMA_API_KEY", "ollama")
    else:
        # Cloud endpoint — real API key is required
        api_key = os.getenv("OLLAMA_API_KEY")
        if not api_key:
            raise EnvironmentError(
                f"OLLAMA_API_KEY not set. "
                f"A real API key is required for cloud Ollama endpoint: {base_url}"
            )

    client = OpenAI(base_url=base_url, api_key=api_key)

    response = client.chat.completions.create(
        model=model,
        max_tokens=max_tokens,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.choices[0].message.content
