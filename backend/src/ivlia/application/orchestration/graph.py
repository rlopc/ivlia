"""The agent graph.

LangGraph stays inside this package: callers pass domain state and get back
the reply as text chunks.
"""

from typing import TYPE_CHECKING, TypedDict

import langsmith
from langgraph.config import get_stream_writer
from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

# LangGraph reads the state annotations at run time.
from ivlia.domain.agents.state import AgentState, Message  # noqa: TC001

if TYPE_CHECKING:
    from collections.abc import AsyncIterator

    from ivlia.domain.models.llm import LLM

# LangGraph traces to LangSmith's cloud when an environment variable such as
# LANGSMITH_TRACING is "true". Conversations must not leave the Mac
# (docs/06), so tracing is off in code, which takes precedence over the
# environment.
langsmith.configure(enabled=False)


class _GraphState(TypedDict):
    messages: list[Message]
    reply: str


type AgentGraph = CompiledStateGraph[_GraphState, None, _GraphState, _GraphState]


def build_graph(llm: LLM) -> AgentGraph:
    async def respond(state: _GraphState) -> dict[str, str]:
        write = get_stream_writer()
        chunks: list[str] = []
        async for chunk in llm.stream(state["messages"]):
            write(chunk)
            chunks.append(chunk)
        return {"reply": "".join(chunks)}

    builder = StateGraph(_GraphState)
    builder.add_node("respond", respond)
    builder.add_edge(START, "respond")
    builder.add_edge("respond", END)
    return builder.compile()


def _to_graph_state(state: AgentState) -> _GraphState:
    return {"messages": list(state.messages), "reply": ""}


async def stream_reply(graph: AgentGraph, state: AgentState) -> AsyncIterator[str]:
    """Run the graph on the conversation and stream the reply chunks."""
    async for chunk in graph.astream(_to_graph_state(state), stream_mode="custom"):
        if isinstance(chunk, str):
            yield chunk
