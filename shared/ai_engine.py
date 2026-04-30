"""
AI engine adapter supporting Ollama and LocalAI (basic).

This module provides a simple `AIEngine` class with a `generate_response`
method. It prefers `AI_ENGINE` environment variable to choose between
implementations. Defaults to `ollama` and expects a local Ollama server
running (default URL: http://localhost:11434).

Note: Endpoints for self-hosted LLM servers vary by version. This adapter
uses a best-effort HTTP call to common Ollama/OpenAI-compatible endpoints
and falls back to returning a readable error message if the call fails.
"""
import os
import logging
from typing import Optional
import requests

logger = logging.getLogger(__name__)


class AIEngine:
    def __init__(self):
        self.engine = os.getenv("AI_ENGINE", "ollama").lower()
        self.ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434")
        self.model = os.getenv("OLLAMA_MODEL", "default")

    def generate_response(self, user_id: str, message: str) -> str:
        """Generate a response from the selected local AI engine.

        Args:
            user_id: The Telegram chat id (used to keep per-user context hints).
            message: The user message to send to the model.

        Returns:
            The model's textual reply, or an error/fallback message.
        """
        if self.engine == "ollama":
            return self._call_ollama(user_id, message)
        if self.engine == "localai":
            return self._call_localai(user_id, message)
        return "❌ AI engine not supported. Set AI_ENGINE to 'ollama' or 'localai'."

    def _call_ollama(self, user_id: str, message: str) -> str:
        url = f"{self.ollama_url}/api/generate"
        system_prompt = "You are an assistant that helps Indonesian farmers with agricultural advice. Keep answers concise and helpful."
        payload = {
            "model": self.model,
            "prompt": f"<SYSTEM>\n{system_prompt}\n<END>\n<User {user_id}>\n{message}",
            "max_tokens": 512,
        }

        try:
            resp = requests.post(url, json=payload, timeout=30)
            resp.raise_for_status()
            # Try to parse JSON response, else return text
            try:
                data = resp.json()
                # Ollama's response shapes vary; try common keys
                if isinstance(data, dict):
                    if "text" in data:
                        return data["text"]
                    if "result" in data and isinstance(data["result"], dict):
                        return data["result"].get("output", resp.text)
                return str(data)
            except ValueError:
                return resp.text
        except requests.RequestException as e:
            logger.error(f"Ollama request failed: {e}")
            return f"❌ Gagal terhubung ke Ollama: {e}"

    def _call_localai(self, user_id: str, message: str) -> str:
        # LocalAI aims to be OpenAI-compatible on /v1 endpoints
        url = os.getenv("LOCALAI_URL", "http://localhost:8080/v1/chat/completions")
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": "You are an assistant for Indonesian farmers."},
                {"role": "user", "content": f"[User {user_id}] {message}"}
            ],
            "max_tokens": 512,
        }

        try:
            resp = requests.post(url, json=payload, timeout=30)
            resp.raise_for_status()
            data = resp.json()
            # OpenAI-style response
            choices = data.get("choices") or []
            if choices:
                first = choices[0]
                if isinstance(first.get("message"), dict):
                    return first["message"].get("content", str(data))
                return first.get("text", str(data))
            return str(data)
        except requests.RequestException as e:
            logger.error(f"LocalAI request failed: {e}")
            return f"❌ Gagal terhubung ke LocalAI: {e}"


# Factory
def get_ai_engine() -> AIEngine:
    return AIEngine()
