"""Backend-only LLM provider abstraction."""

import json
import logging
import os
from typing import Any

logger = logging.getLogger(__name__)

OpenAI = None  # Loaded lazily so embedding-only workflows do not require the SDK.


class LLMConfigurationError(RuntimeError):
    """Raised when the configured LLM cannot be used."""


class LLMGenerationError(RuntimeError):
    """Raised when the provider fails to generate a response."""


class LLMService:
    def __init__(self) -> None:
        self.provider = os.getenv("LLM_PROVIDER", "openai").lower()
        self.model = os.getenv("LLM_MODEL", os.getenv("OPENAI_MODEL", "gpt-4o-mini"))
        self.api_key = os.getenv("LLM_API_KEY", os.getenv("OPENAI_API_KEY", ""))
        self.base_url = os.getenv("LLM_BASE_URL", os.getenv("OPENAI_BASE_URL", ""))

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        if not self.api_key:
            raise LLMConfigurationError("LLM API key is not configured on the backend")
        if self.provider not in ["openai", "groq"]:
            raise LLMConfigurationError(f"Unsupported LLM provider: {self.provider}")
        global OpenAI
        if OpenAI is None:
            try:
                from openai import OpenAI as OpenAIClient
                OpenAI = OpenAIClient
            except ImportError as exc:
                raise LLMConfigurationError("The configured LLM provider dependency is not installed") from exc
        if OpenAI is None:
            raise LLMConfigurationError("The configured LLM provider dependency is not installed")

        try:
            kwargs: dict[str, Any] = {"api_key": self.api_key}
            
            # Configure base_url for Groq compatibility
            if self.provider == "groq" and not self.base_url:
                kwargs["base_url"] = "https://api.groq.com/openai/v1"
            elif self.base_url:
                kwargs["base_url"] = self.base_url
                
            client = OpenAI(**kwargs)
            response = client.chat.completions.create(
                model=self.model,
                temperature=0.2,
                max_tokens=512,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
            )
            content = response.choices[0].message.content
            if not content:
                raise LLMGenerationError("The LLM returned an empty response")
                
            import re
            content = re.sub(r'<think>.*?</think>', '', content, flags=re.DOTALL)
            
            return content.strip()
        except LLMGenerationError:
            raise
        except Exception as exc:
            logger.warning("LLM provider request failed: %s", exc.__class__.__name__)
            if hasattr(exc, "response"):
                logger.error(f"Error detail: {exc.response.text}")
            raise LLMGenerationError("The LLM provider could not complete the request") from exc

    def generate_json(self, system_prompt: str, user_prompt: str) -> dict[str, Any]:
        response = self.generate(system_prompt, user_prompt)
        try:
            return json.loads(response)
        except json.JSONDecodeError as exc:
            raise LLMGenerationError("The LLM returned invalid structured data") from exc


_service: LLMService | None = None


def get_llm_service() -> LLMService:
    global _service
    if _service is None:
        _service = LLMService()
    return _service