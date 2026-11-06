import asyncio
import json
from types import SimpleNamespace

import pytest

from connoisseur_companion.agent import RestaurantAgent


class FakeOllama:
    """Replays scripted responses and records the messages it was sent."""

    def __init__(self, responses):
        self._responses = list(responses)
        self.calls = []

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        return None

    async def chat_messages(self, messages, tools):
        self.calls.append(([dict(m) for m in messages], tools))
        return self._responses.pop(0)


class FakeMCP:
    def __init__(self, result=None):
        self.result = result or SimpleNamespace(
            structuredContent={"name": "Iron & Embers"}, content=[], isError=False
        )
        self.tool_calls = []

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        return None

    async def list_tools(self):
        return [
            SimpleNamespace(
                name="get_restaurant_info",
                description="info",
                inputSchema={"type": "object"},
            )
        ]

    async def call_tool(self, name, arguments):
        self.tool_calls.append((name, arguments))
        return self.result


def reply(content="", calls=()):
    tool_calls = [
        SimpleNamespace(function=SimpleNamespace(name=n, arguments=a)) for n, a in calls
    ]
    message = SimpleNamespace(
        content=content,
        tool_calls=tool_calls or None,
        model_dump=lambda exclude_none=True: {
            "role": "assistant",
            "content": content,
        },
    )
    return SimpleNamespace(message=message)


def run(agent, prompt, history=None):
    return asyncio.run(agent.answer(prompt, history))


def test_returns_content_when_no_tool_calls():
    agent = RestaurantAgent(FakeOllama([reply("Hello!")]), FakeMCP())
    assert run(agent, "hi") == "Hello!"


def test_executes_tool_and_feeds_result_back():
    ollama = FakeOllama(
        [
            reply(calls=[("get_restaurant_info", {"item_id": 1000001})]),
            reply("It is Iron & Embers."),
        ]
    )
    mcp = FakeMCP()
    answer = run(RestaurantAgent(ollama, mcp), "tell me about 1000001")

    assert answer == "It is Iron & Embers."
    assert mcp.tool_calls == [("get_restaurant_info", {"item_id": 1000001})]
    tool_message = ollama.calls[1][0][-1]
    assert tool_message["role"] == "tool"
    assert json.loads(tool_message["content"]) == {"name": "Iron & Embers"}


def test_unknown_tool_returns_error_to_model_instead_of_crashing():
    ollama = FakeOllama(
        [reply(calls=[("made_up_tool", {})]), reply("Sorry, recovered.")]
    )
    mcp = FakeMCP()
    answer = run(RestaurantAgent(ollama, mcp), "hi")

    assert answer == "Sorry, recovered."
    assert mcp.tool_calls == []
    error = json.loads(ollama.calls[1][0][-1]["content"])
    assert "made_up_tool" in error["error"]


def test_tool_error_is_wrapped():
    mcp = FakeMCP(
        SimpleNamespace(structuredContent={"msg": "bad"}, content=[], isError=True)
    )
    ollama = FakeOllama(
        [reply(calls=[("get_restaurant_info", {})]), reply("done")]
    )
    run(RestaurantAgent(ollama, mcp), "hi")
    assert json.loads(ollama.calls[1][0][-1]["content"]) == {"error": {"msg": "bad"}}


def test_stops_after_max_tool_rounds():
    ollama = FakeOllama(
        [reply(calls=[("get_restaurant_info", {})]) for _ in range(2)]
    )
    agent = RestaurantAgent(ollama, FakeMCP(), max_tool_rounds=2)
    assert "limit" in run(agent, "loop forever")
    assert len(ollama.calls) == 2


def test_history_keeps_only_string_user_and_assistant_turns():
    ollama = FakeOllama([reply("ok")])
    history = [
        {"role": "user", "content": "earlier"},
        {"role": "assistant", "content": "answer"},
        {"role": "tool", "content": "ignored"},
        {"role": "user", "content": [{"type": "image"}]},
    ]
    run(RestaurantAgent(ollama, FakeMCP()), "now", history)
    roles = [m["role"] for m in ollama.calls[0][0]]
    assert roles == ["system", "user", "assistant", "user"]


def test_rejects_invalid_max_tool_rounds():
    with pytest.raises(ValueError):
        RestaurantAgent(FakeOllama([]), FakeMCP(), max_tool_rounds=0)
