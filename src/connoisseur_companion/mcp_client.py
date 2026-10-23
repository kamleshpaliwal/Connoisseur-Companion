"""Reusable stdio client for the local Connoisseur Companion MCP server."""

from __future__ import annotations

import sys
from contextlib import AsyncExitStack
from pathlib import Path
from typing import Any

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.types import CallToolResult, Tool


class MCPClient:
    """Manage a connection to an MCP server and expose discovery and tool calls."""

    def __init__(self, server: StdioServerParameters | None = None) -> None:
        project_root = Path(__file__).resolve().parents[2]
        self._server = server or StdioServerParameters(
            command=sys.executable,
            args=["-m", "connoisseur_companion.mcp_server"],
            cwd=project_root,
        )
        self._exit_stack = AsyncExitStack()
        self._session: ClientSession | None = None

    async def __aenter__(self) -> MCPClient:
        try:
            read_stream, write_stream = await self._exit_stack.enter_async_context(
                stdio_client(self._server)
            )
            self._session = await self._exit_stack.enter_async_context(
                ClientSession(read_stream, write_stream)
            )
            await self._session.initialize()
        except BaseException:
            await self._exit_stack.aclose()
            raise
        return self

    async def __aexit__(self, exc_type: Any, exc: Any, traceback: Any) -> None:
        self._session = None
        await self._exit_stack.aclose()

    async def list_tools(self) -> list[Tool]:
        """Return the tools currently exposed by the connected server."""
        return (await self._get_session().list_tools()).tools

    async def call_tool(
        self, name: str, arguments: dict[str, Any] | None = None
    ) -> CallToolResult:
        """Call an MCP tool and return its structured protocol result."""
        return await self._get_session().call_tool(name, arguments=arguments or {})

    def _get_session(self) -> ClientSession:
        if self._session is None:
            raise RuntimeError("MCPClient must be used inside 'async with'.")
        return self._session
