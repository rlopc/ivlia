"""An LLM adapter that always replies with a fixed greeting."""

from typing import TYPE_CHECKING

from ivlia.domain.data_policy.levels import DataLevel

if TYPE_CHECKING:
    from collections.abc import AsyncIterator, Sequence

    from ivlia.domain.agents.state import Message

REPLY_CHUNKS = ("Hello", ", ", "world", "!")


class HelloWorldLLM:
    @property
    def max_data_level(self) -> DataLevel:
        # Runs in process, so it may receive anything that stays on the Mac.
        return DataLevel.PRIVATE

    async def stream(self, messages: Sequence[Message]) -> AsyncIterator[str]:  # noqa: ARG002
        for chunk in REPLY_CHUNKS:
            yield chunk
