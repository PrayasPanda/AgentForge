"""
Unified LLM client — supports Anthropic Claude, Ollama (local or cloud), and Google Gemini.

Configure via environment variables:

  # Choose provider (default: anthropic)
  LLM_PROVIDER=anthropic   # or: ollama, gemini

  # Anthropic
  ANTHROPIC_API_KEY=sk-ant-...

  # Ollama — LOCAL (no API key needed)
  OLLAMA_BASE_URL=http://localhost:11434/v1
  OLLAMA_MODEL=llama3.2

  # Ollama — CLOUD (real API key required)
  OLLAMA_BASE_URL=https://your-cloud-host/v1
  OLLAMA_MODEL=llama3.2
  OLLAMA_API_KEY=your-real-cloud-api-key

  # Google Gemini
  GEMINI_API_KEY=AIza...
  GEMINI_MODEL=gemini-2.0-flash        # optional, default: gemini-2.0-flash
  GEMINI_MODEL_FAST=gemini-2.0-flash   # optional, default: gemini-2.0-flash

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
        fast: Use a smaller/faster model (Haiku for Anthropic; flash for Gemini).

    Returns:
        Response text as a plain string.
    """
    if PROVIDER == "ollama":
        return _ollama_complete(prompt, max_tokens)
    if PROVIDER == "gemini":
        return _gemini_complete(prompt, max_tokens, fast)
    return _anthropic_complete(prompt, max_tokens, fast)


def provider_label() -> str:
    """Human-readable description of the active provider (for CLI output)."""
    if PROVIDER == "ollama":
        model = os.getenv("OLLAMA_MODEL", "llama3.2")
        base = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1")
        host = base.replace("/v1", "").rstrip("/")
        mode = "local" if _is_ollama_local() else "cloud"
        return f"Ollama {mode} ({model} @ {host})"
    if PROVIDER == "gemini":
        model = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
        return f"Google Gemini ({model})"
    return f"Anthropic ({_ANTHROPIC_MODELS['default']})"


# ── Anthropic ────────────────────────────────────────────────────────────────

def _anthropic_complete(prompt: str, max_tokens: int, fast: bool) -> str:
    import anthropic as _anthropic

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise EnvironmentError(
            "ANTHROPIC_API_KEY not set. "
            "Copy .env.example to .env and add your key, "
            "or set LLM_PROVIDER=ollama / LLM_PROVIDER=gemini to use another provider."
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
        api_key = os.getenv("OLLAMA_API_KEY", "ollama")
    else:
        api_key = os.getenv("OLLAMA_API_KEY")
        if not api_key:
            raise EnvironmentError(
                f"OLLAMA_API_KEY not set. "
                f"A real API key is required for cloud Ollama endpoint: {base_url}"
            )

    client = OpenAI(base_url=base_url, api_key=api_key)

    chunks = client.chat.completions.create(
        model=model,
        max_tokens=max_tokens,
        messages=[{"role": "user", "content": prompt}],
        stream=True,
    )

    result = []
    token_count = 0
    print("   Streaming response", end="", flush=True)
    for chunk in chunks:
        delta = chunk.choices[0].delta.content
        if delta:
            result.append(delta)
            token_count += 1
            if token_count % 20 == 0:
                print(f"\r   Streaming response... {token_count} tokens", end="", flush=True)
    print(f"\r   Done — {token_count} tokens received.          ")

    return "".join(result)


# ── Google Gemini ─────────────────────────────────────────────────────────────

def _gemini_complete(prompt: str, max_tokens: int, fast: bool) -> str:
    import json
    import threading
    import urllib.request
    import urllib.error

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise EnvironmentError(
            "GEMINI_API_KEY not set. "
            "Get your key at https://aistudio.google.com/apikey and set GEMINI_API_KEY in .env"
        )

    model = (
        os.getenv("GEMINI_MODEL_FAST", "gemini-3.1-flash-lite")
        if fast
        else os.getenv("GEMINI_MODEL", "gemini-3.1-flash-lite")
    )

    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/"
        f"{model}:generateContent?key={api_key}"
    )
    body = json.dumps({
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"maxOutputTokens": max_tokens},
    }).encode()
    req = urllib.request.Request(
        url, data=body, headers={"Content-Type": "application/json"}
    )

    # Background spinner so the user sees progress
    done = threading.Event()
    def _spin():
        elapsed = 0
        while not done.wait(2):
            elapsed += 2
            print(f"\r   Waiting for Gemini ({model})... {elapsed}s", end="", flush=True)

    print(f"   Waiting for Gemini ({model})...", end="", flush=True)
    spinner = threading.Thread(target=_spin, daemon=True)
    spinner.start()

    try:
        with urllib.request.urlopen(req, timeout=180) as resp:
            data = json.load(resp)
        done.set()
        spinner.join()
        print(f"\r   Done!                                              ")
        return data["candidates"][0]["content"]["parts"][0]["text"]
    except urllib.error.HTTPError as e:
        done.set()
        spinner.join()
        raise RuntimeError(f"Gemini API error {e.code}: {e.read().decode()}") from e
    except Exception:
        done.set()
        spinner.join()
        raise
