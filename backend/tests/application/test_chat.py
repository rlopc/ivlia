import asyncio
from typing import TYPE_CHECKING

from ivlia.adapters.hello_world_llm import REPLY_CHUNKS, HelloWorldLLM
from ivlia.application.chat import REPLY_FAILED, Chat
from ivlia.application.orchestration.graph import build_graph
from ivlia.contract.events import EndEvent, ErrorEvent, Event, TokenEvent
from ivlia.domain.agents.state import AgentState, Message
from ivlia.domain.data_policy.levels import DataLevel

if TYPE_CHECKING:
    from collections.abc import AsyncIterator, Sequence

    import pytest

    from ivlia.domain.models.llm import LLM

STATE = AgentState(messages=(Message(role="user", content="Hi"),))


class _ModelCrashedError(RuntimeError):
    def __init__(self) -> None:
        super().__init__("model crashed")


class _FailingLLM:
    @property
    def max_data_level(self) -> DataLevel:
        return DataLevel.PRIVATE

    async def stream(self, messages: Sequence[Message]) -> AsyncIterator[str]:  # noqa: ARG002
        yield "Hel"
        raise _ModelCrashedError


def _events(llm: LLM) -> list[Event]:
    async def collect() -> list[Event]:
        return [event async for event in Chat(build_graph(llm))(STATE)]

    return asyncio.run(collect())


def test_reply_streams_tokens_then_end(caplog: pytest.LogCaptureFixture) -> None:
    expected: list[Event] = [TokenEvent(text=chunk) for chunk in REPLY_CHUNKS]

    assert _events(HelloWorldLLM()) == [*expected, EndEvent()]
    [record] = [r for r in caplog.records if r.getMessage() == "Chat reply sent"]
    assert record.__dict__["chunks"] == len(REPLY_CHUNKS)


def test_failure_ends_the_stream_with_an_error(
    caplog: pytest.LogCaptureFixture,
) -> None:
    events = _events(_FailingLLM())

    assert events[-1] == ErrorEvent(message=REPLY_FAILED)
    assert EndEvent() not in events
    assert "model crashed" in caplog.text
