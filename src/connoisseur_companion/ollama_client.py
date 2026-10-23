"""Small asynchronous chat client for the local Ollama service."""

from __future__ import annotations

from types import TracebackType

from ollama import AsyncClient


DEFAULT_OLLAMA_HOST = "http://localhost:11434"
DEFAULT_OLLAMA_MODEL = "qwen3:4b-instruct"


class OllamaChatClient:
    """Send chat messages to an already-installed local Ollama model."""

    def __init__(
        self,
        model: str = DEFAULT_OLLAMA_MODEL,
        host: str = DEFAULT_OLLAMA_HOST,
    ) -> None:
        self.model = model
        self._client = AsyncClient(host=host)

    async def __aenter__(self) -> OllamaChatClient:
        await self._client.__aenter__()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        await self._client.__aexit__(exc_type, exc, traceback)

    async def chat(self, prompt: str, system_prompt: str | None = None) -> str:
        """Return one non-streaming response from the configured local model."""
        messages: list[dict[str, str]] = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        response = await self._client.chat(
            model=self.model,
            messages=messages,
            stream=False,
        )
        return response.message.content
