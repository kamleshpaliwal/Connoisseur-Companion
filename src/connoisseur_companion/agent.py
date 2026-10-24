"""Bounded ReAct-style coordinator connecting Ollama to the MCP tools."""

from __future__ import annotations

import json
from typing import Any

from connoisseur_companion.mcp_client import MCPClient
from connoisseur_companion.ollama_client import OllamaChatClient


SYSTEM_PROMPT = """You are Connoisseur Companion, an assistant for California restaurants.
Use the available tools to look up factual restaurant details, atmosphere matches,
and reviews. Do not invent data. Explain when the data has no matching result."""
MAX_TOOL_ROUNDS = 4


class RestaurantAgent:
    """Coordinate model reasoning and restaurant tool execution over MCP."""

    def __init__(
        self,
        ollama_client: OllamaChatClient | None = None,
        mcp_client: MCPClient | None = None,
        max_tool_rounds: int = MAX_TOOL_ROUNDS,
    ) -> None:
        if max_tool_rounds < 1:
            raise ValueError("max_tool_rounds must be at least 1")
        self._ollama = ollama_client or OllamaChatClient()
        self._mcp = mcp_client or MCPClient()
        self._max_tool_rounds = max_tool_rounds

    async def answer(
        self, prompt: str, history: list[dict[str, Any]] | None = None
    ) -> str:
        """Answer a user prompt, executing model-requested MCP tools as needed."""
        async with self._ollama, self._mcp:
            discovered_tools = await self._mcp.list_tools()
            tools = [
                {
                    "type": "function",
                    "function": {
                        "name": tool.name,
                        "description": tool.description or "",
                        "parameters": tool.inputSchema,
                    },
                }
                for tool in discovered_tools
            ]
            allowed_tools = {tool.name for tool in discovered_tools}
            messages: list[dict[str, Any]] = [
                {"role": "system", "content": SYSTEM_PROMPT},
            ]
            for turn in history or []:
                role = turn.get("role")
                content = turn.get("content")
                if role in {"user", "assistant"} and isinstance(content, str):
                    messages.append({"role": role, "content": content})
            messages.append({"role": "user", "content": prompt})

            for _ in range(self._max_tool_rounds):
                response = await self._ollama.chat_messages(messages, tools)
                assistant_message = response.message.model_dump(exclude_none=True)
                messages.append(assistant_message)
                tool_calls = response.message.tool_calls or []
                if not tool_calls:
                    return response.message.content or "I could not produce an answer."

                for call in tool_calls:
                    name = call.function.name
                    if name not in allowed_tools:
                        raise ValueError(f"Model requested an unknown MCP tool: {name}")
                    result = await self._mcp.call_tool(
                        name, arguments=call.function.arguments
                    )
                    payload = (
                        result.structuredContent
                        if result.structuredContent is not None
                        else [block.model_dump(exclude_none=True) for block in result.content]
                    )
                    if result.isError:
                        payload = {"error": payload}
                    messages.append(
                        {
                            "role": "tool",
                            "tool_name": name,
                            "content": json.dumps(payload, ensure_ascii=False),
                        }
                    )

            return (
                "I reached the limit for restaurant lookups. Please refine your "
                "request or ask about one restaurant at a time."
            )
