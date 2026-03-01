"""Direct Ollama provider with proper tool calling support."""

import json
from typing import Any

import httpx

from nanobot.providers.base import LLMProvider, LLMResponse, ToolCallRequest


class OllamaProvider(LLMProvider):
    """
    Direct Ollama provider that bypasses LiteLLM for better tool calling support.

    Uses Ollama's native /api/chat endpoint with proper tool calling format.
    """

    def __init__(
        self,
        api_key: str | None = None,
        api_base: str = "http://localhost:11434",
    ):
        super().__init__(api_key, api_base or "http://localhost:11434")
        self._client = httpx.AsyncClient(timeout=120.0)

    async def chat(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        model: str = "qwen3:14b",
        max_tokens: int = 4096,
        temperature: float = 0.7,
    ) -> LLMResponse:
        """
        Send chat completion request to Ollama.

        Args:
            messages: List of message dicts
            tools: Optional list of tool definitions
            model: Model name (without ollama/ prefix)
            max_tokens: Max tokens in response
            temperature: Sampling temperature

        Returns:
            LLMResponse with content and/or tool calls
        """
        # Remove ollama/ prefix if present
        model = model.replace("ollama/", "")

        # Convert messages to Ollama format
        # Handle tool role messages differently
        ollama_messages = []
        for msg in messages:
            if msg.get("role") == "tool":
                # Ollama expects "tool" role with "content" field, not "tool_call_id"
                ollama_messages.append({
                    "role": "tool",
                    "content": msg.get("content", ""),
                    "tool_name": msg.get("name", ""),  # Ollama uses tool_name instead of name
                })
            else:
                ollama_messages.append(msg)

        payload = {
            "model": model,
            "messages": ollama_messages,
            "stream": False,
        }

        # Add tools if provided
        if tools:
            payload["tools"] = tools

        try:
            response = await self._client.post(
                f"{self.api_base}/api/chat",
                json=payload,
                headers={"Content-Type": "application/json"},
            )
            response.raise_for_status()
            data = response.json()
            return self._parse_response(data)

        except Exception as e:
            return LLMResponse(
                content=f"Error calling Ollama: {str(e)}",
                finish_reason="error",
            )

    def _parse_response(self, data: dict[str, Any]) -> LLMResponse:
        """Parse Ollama response into LLMResponse."""
        message = data.get("message", {})
        content = message.get("content", "")
        tool_calls = []

        # Parse tool calls
        raw_tool_calls = message.get("tool_calls", [])
        for tc in raw_tool_calls:
            func = tc.get("function", {})
            tool_calls.append(
                ToolCallRequest(
                    id=tc.get("id", ""),
                    name=func.get("name", ""),
                    arguments=func.get("arguments", {}),
                )
            )

        return LLMResponse(
            content=content or None,
            tool_calls=tool_calls,
            finish_reason=data.get("done_reason", "stop"),
        )

    async def close(self):
        """Close the HTTP client."""
        await self._client.aclose()

    def get_default_model(self) -> str:
        """Return default model name."""
        return "qwen3:14b"
