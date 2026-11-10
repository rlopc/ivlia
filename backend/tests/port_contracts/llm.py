import asyncio

import pytest

from ivlia.domain.agents.state import Message
from ivlia.domain.data_policy.levels import DataLevel
from ivlia.domain.models.llm import LLM

CONVERSATION = (Message(role="user", content="Hi"),)


async def _collect(llm: LLM) -> list[str]:
    return [chunk async for chunk in llm.stream(CONVERSATION)]


class LLMContract:
    @pytest.fixture
    def adapter(self) -> LLM:
        raise NotImplementedError

    def test_implements_the_port(self, adapter: LLM) -> None:
        assert isinstance(adapter, LLM)

    def test_declares_a_data_level(self, adapter: LLM) -> None:
        assert isinstance(adapter.max_data_level, DataLevel)

    def test_never_accepts_secret_data(self, adapter: LLM) -> None:
        assert adapter.max_data_level < DataLevel.SECRET

    def test_streams_a_non_empty_text_reply(self, adapter: LLM) -> None:
        chunks = asyncio.run(_collect(adapter))

        assert chunks
        assert all(isinstance(chunk, str) for chunk in chunks)
        assert "".join(chunks)
