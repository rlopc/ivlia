import asyncio

from ivlia.adapters.hello_world_llm import REPLY_CHUNKS, HelloWorldLLM
from ivlia.application.orchestration.graph import build_graph, stream_reply
from ivlia.domain.agents.state import AgentState, Message


async def _collect() -> list[str]:
    graph = build_graph(HelloWorldLLM())
    state = AgentState(messages=(Message(role="user", content="Hi"),))
    return [chunk async for chunk in stream_reply(graph, state)]


def test_graph_streams_the_llm_chunks_in_order() -> None:
    assert asyncio.run(_collect()) == list(REPLY_CHUNKS)
