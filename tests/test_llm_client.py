"""
Unit tests for llm_client.py — provider selection and label logic.
Does NOT make real API calls; patches the underlying SDK clients.
"""

import os
import importlib
import unittest.mock as mock

import pytest


# ── provider_label ────────────────────────────────────────────────────────────

def _reload_client_with_env(env: dict):
    """Reload llm_client with a controlled environment."""
    with mock.patch.dict(os.environ, env, clear=False):
        import src.llm_client as mod
        importlib.reload(mod)
        return mod


class TestProviderLabel:
    def test_anthropic_label_contains_sonnet(self):
        mod = _reload_client_with_env({"LLM_PROVIDER": "anthropic"})
        label = mod.provider_label()
        assert "Anthropic" in label
        assert "sonnet" in label.lower() or "claude" in label.lower()

    def test_ollama_label_contains_model_name(self):
        mod = _reload_client_with_env({
            "LLM_PROVIDER": "ollama",
            "OLLAMA_MODEL": "llama3.2",
            "OLLAMA_BASE_URL": "http://localhost:11434/v1",
        })
        label = mod.provider_label()
        assert "Ollama" in label
        assert "llama3.2" in label

    def test_ollama_label_strips_v1_from_host(self):
        mod = _reload_client_with_env({
            "LLM_PROVIDER": "ollama",
            "OLLAMA_BASE_URL": "http://localhost:11434/v1",
            "OLLAMA_MODEL": "mistral",
        })
        label = mod.provider_label()
        assert "/v1" not in label
        assert "localhost:11434" in label

    def test_default_provider_is_anthropic(self):
        env = {k: v for k, v in os.environ.items() if k != "LLM_PROVIDER"}
        with mock.patch.dict(os.environ, env, clear=True):
            import src.llm_client as mod
            importlib.reload(mod)
            assert mod.PROVIDER == "anthropic"


# ── routing ───────────────────────────────────────────────────────────────────

class TestProviderRouting:
    def test_anthropic_route_calls_anthropic(self):
        mod = _reload_client_with_env({"LLM_PROVIDER": "anthropic"})
        with mock.patch.object(mod, "_anthropic_complete", return_value="ok") as m:
            result = mod.complete("hello", max_tokens=10, fast=False)
        m.assert_called_once_with("hello", 10, False)
        assert result == "ok"

    def test_anthropic_fast_flag_passed_through(self):
        mod = _reload_client_with_env({"LLM_PROVIDER": "anthropic"})
        with mock.patch.object(mod, "_anthropic_complete", return_value="ok") as m:
            mod.complete("hello", max_tokens=5, fast=True)
        _, _, fast_arg = m.call_args[0]
        assert fast_arg is True

    def test_ollama_route_calls_ollama(self):
        mod = _reload_client_with_env({"LLM_PROVIDER": "ollama"})
        with mock.patch.object(mod, "_ollama_complete", return_value="ok") as m:
            result = mod.complete("hello", max_tokens=10)
        m.assert_called_once_with("hello", 10)
        assert result == "ok"

    def test_unknown_provider_falls_back_to_anthropic(self):
        # Any unrecognised value should fall through to anthropic branch
        mod = _reload_client_with_env({"LLM_PROVIDER": "gpt4"})
        with mock.patch.object(mod, "_anthropic_complete", return_value="ok") as m:
            mod.complete("hello")
        m.assert_called_once()


# ── error handling ────────────────────────────────────────────────────────────

class TestAnthropicMissingKey:
    def test_raises_environment_error_when_key_missing(self):
        mod = _reload_client_with_env({"LLM_PROVIDER": "anthropic"})
        env_without_key = {k: v for k, v in os.environ.items() if k != "ANTHROPIC_API_KEY"}
        with mock.patch.dict(os.environ, env_without_key, clear=True):
            with pytest.raises(EnvironmentError, match="ANTHROPIC_API_KEY"):
                mod._anthropic_complete("test", 100, False)


# ── local vs cloud detection ──────────────────────────────────────────────────

class TestOllamaLocalVsCloud:
    def test_localhost_detected_as_local(self):
        mod = _reload_client_with_env({"OLLAMA_BASE_URL": "http://localhost:11434/v1"})
        assert mod._is_ollama_local() is True

    def test_127_detected_as_local(self):
        mod = _reload_client_with_env({"OLLAMA_BASE_URL": "http://127.0.0.1:11434/v1"})
        assert mod._is_ollama_local() is True

    def test_cloud_url_detected_as_cloud(self):
        import src.llm_client as mod
        assert mod._is_ollama_local("https://api.myserver.com/v1") is False

    def test_label_shows_local_for_localhost(self):
        mod = _reload_client_with_env({
            "LLM_PROVIDER": "ollama",
            "OLLAMA_BASE_URL": "http://localhost:11434/v1",
            "OLLAMA_MODEL": "llama3.2",
        })
        with mock.patch.dict(os.environ, {"OLLAMA_BASE_URL": "http://localhost:11434/v1"}):
            label = mod.provider_label()
        assert "local" in label

    def test_label_shows_cloud_for_remote_url(self):
        mod = _reload_client_with_env({
            "LLM_PROVIDER": "ollama",
            "OLLAMA_BASE_URL": "https://api.myserver.com/v1",
            "OLLAMA_MODEL": "llama3.2",
        })
        with mock.patch.dict(os.environ, {
            "OLLAMA_BASE_URL": "https://api.myserver.com/v1",
            "OLLAMA_MODEL": "llama3.2",
        }):
            label = mod.provider_label()
        assert "cloud" in label

    def test_cloud_raises_when_api_key_missing(self):
        mod = _reload_client_with_env({
            "LLM_PROVIDER": "ollama",
            "OLLAMA_BASE_URL": "https://api.myserver.com/v1",
            "OLLAMA_MODEL": "llama3.2",
        })
        env_without_key = {
            k: v for k, v in os.environ.items() if k != "OLLAMA_API_KEY"
        }
        env_without_key["OLLAMA_BASE_URL"] = "https://api.myserver.com/v1"
        with mock.patch.dict(os.environ, env_without_key, clear=True):
            with pytest.raises(EnvironmentError, match="OLLAMA_API_KEY"):
                mod._ollama_complete("test", 100)

    def test_local_does_not_require_api_key(self):
        mod = _reload_client_with_env({
            "LLM_PROVIDER": "ollama",
            "OLLAMA_BASE_URL": "http://localhost:11434/v1",
            "OLLAMA_MODEL": "llama3.2",
        })
        env_without_key = {
            k: v for k, v in os.environ.items() if k != "OLLAMA_API_KEY"
        }
        env_without_key["OLLAMA_BASE_URL"] = "http://localhost:11434/v1"
        # Should not raise — patches OpenAI to avoid a real network call
        with mock.patch.dict(os.environ, env_without_key, clear=True):
            with mock.patch("openai.OpenAI") as mock_openai:
                mock_client = mock.MagicMock()
                mock_openai.return_value = mock_client
                mock_client.chat.completions.create.return_value = mock.MagicMock(
                    choices=[mock.MagicMock(message=mock.MagicMock(content="ok"))]
                )
                result = mod._ollama_complete("test", 100)
        assert result == "ok"


# ── OLLAMA_MODEL default ──────────────────────────────────────────────────────

class TestOllamaDefaults:
    def test_default_model_is_llama(self):
        env = {k: v for k, v in os.environ.items() if k != "OLLAMA_MODEL"}
        with mock.patch.dict(os.environ, {"LLM_PROVIDER": "ollama"}, clear=False):
            import src.llm_client as mod
            importlib.reload(mod)
            label = mod.provider_label()
        assert "llama" in label.lower()
