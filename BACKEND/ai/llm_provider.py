import os
from abc import ABC, abstractmethod
from typing import Optional
import httpx
from backend.app.config import settings


class LLMError(Exception):
    """Base exception for LLM provider failures."""
    def __init__(self, reason: str, message: str = ""):
        self.reason = reason
        super().__init__(message or reason)


class LLMTimeoutError(LLMError):
    def __init__(self, message: str = "Request timed out"):
        super().__init__("timeout", message)


class LLMNetworkError(LLMError):
    def __init__(self, message: str = "Network connection failed"):
        super().__init__("network_error", message)


class LLMHTTPError(LLMError):
    def __init__(self, status_code: int, message: str = ""):
        self.status_code = status_code
        super().__init__(f"http_error_{status_code}", message or f"HTTP error {status_code}")


class LLMEmptyResponseError(LLMError):
    def __init__(self, message: str = "Empty response returned by model"):
        super().__init__("empty_response", message)


class BaseLLMProvider(ABC):
    """Abstract interface for LLM inference providers."""

    @abstractmethod
    def is_configured(self) -> bool:
        """Return True if required API keys and model parameters are set."""
        pass

    @abstractmethod
    def get_unconfigured_reason(self) -> Optional[str]:
        """Return specific fallback reason if unconfigured (e.g. missing_api_key, missing_model, provider_none)."""
        pass

    @abstractmethod
    def generate(self, system_prompt: str, user_prompt: str) -> str:
        """Generate a completion response given system and user prompts."""
        pass


class NoneProvider(BaseLLMProvider):
    """Fallback no-op provider when LLM integration is disabled or unconfigured."""

    def is_configured(self) -> bool:
        return False

    def get_unconfigured_reason(self) -> Optional[str]:
        return "provider_none"

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        raise LLMError("provider_none", "LLM provider is set to none.")


class GroqProvider(BaseLLMProvider):
    """
    Groq LLM provider utilizing OpenAI-compatible chat completions endpoint via httpx.
    Configured ONLY through environment variables / settings.
    Never logs credentials or model names.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout_seconds: Optional[float] = None,
    ):
        raw_key = api_key if api_key is not None else (settings.GROQ_API_KEY or os.getenv("GROQ_API_KEY", ""))
        self.api_key = raw_key.strip()

        raw_model = model if model is not None else (settings.GROQ_MODEL or os.getenv("GROQ_MODEL", ""))
        self.model = raw_model.strip()

        raw_base_url = base_url if base_url is not None else (settings.GROQ_BASE_URL or os.getenv("GROQ_BASE_URL", "https://api.groq.com/openai/v1"))
        self.base_url = raw_base_url.rstrip("/")

        raw_timeout = timeout_seconds if timeout_seconds is not None else (settings.LLM_TIMEOUT_SECONDS or os.getenv("LLM_TIMEOUT_SECONDS", "15.0"))
        try:
            self.timeout = float(raw_timeout)
        except (ValueError, TypeError):
            self.timeout = 15.0

    def get_unconfigured_reason(self) -> Optional[str]:
        if not self.api_key:
            return "missing_api_key"
        if not self.model:
            return "missing_model"
        return None

    def is_configured(self) -> bool:
        return self.get_unconfigured_reason() is None

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        unconfigured_reason = self.get_unconfigured_reason()
        if unconfigured_reason:
            raise LLMError(unconfigured_reason, f"Groq provider is not fully configured: {unconfigured_reason}")

        endpoint = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.0,
        }

        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(endpoint, json=payload, headers=headers)
                if response.status_code != 200:
                    raise LLMHTTPError(response.status_code, f"Groq returned HTTP {response.status_code}")
                data = response.json()
        except httpx.TimeoutException as e:
            raise LLMTimeoutError(str(e))
        except httpx.RequestError as e:
            raise LLMNetworkError(str(e))

        choices = data.get("choices")
        if not choices or not isinstance(choices, list) or len(choices) == 0:
            raise LLMEmptyResponseError("No choices returned in completion payload.")

        first_choice = choices[0] or {}
        message = first_choice.get("message") or {}
        content = message.get("content")
        if content is None or not str(content).strip():
            raise LLMEmptyResponseError("Empty content string returned in message.")

        return str(content).strip()


def get_llm_provider() -> BaseLLMProvider:
    """
    Factory function instantiating the configured provider.
    Adding another provider in the future only requires a new class and mapping here.
    """
    provider_name = (settings.LLM_PROVIDER or os.getenv("LLM_PROVIDER", "none")).strip().lower()
    if provider_name == "groq":
        return GroqProvider()
    return NoneProvider()
