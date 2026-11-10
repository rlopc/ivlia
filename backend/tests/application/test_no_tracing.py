import asyncio
import socket
from typing import TYPE_CHECKING

from langchain_core.tracers.langchain import wait_for_all_tracers

from ivlia.adapters.hello_world_llm import HelloWorldLLM
from ivlia.application.orchestration.graph import build_graph, stream_reply
from ivlia.domain.agents.state import AgentState, Message

if TYPE_CHECKING:
    import pytest


async def _run() -> None:
    graph = build_graph(HelloWorldLLM())
    state = AgentState(messages=(Message(role="user", content="Hi"),))
    async for _ in stream_reply(graph, state):
        pass


def test_graph_sends_nothing_even_with_tracing_enabled(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    for name in ("LANGSMITH_TRACING", "LANGCHAIN_TRACING_V2"):
        monkeypatch.setenv(name, "true")
    monkeypatch.setenv("LANGSMITH_API_KEY", "not-a-real-key")
    attempts: list[object] = []

    def blocked_connect(_sock: socket.socket, address: object) -> None:
        attempts.append(address)
        raise ConnectionRefusedError

    monkeypatch.setattr(socket.socket, "connect", blocked_connect)

    asyncio.run(_run())
    wait_for_all_tracers()

    assert attempts == []
