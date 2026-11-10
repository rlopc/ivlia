"""The chat use case: one turn of the conversation as contract events."""

import logging
import time
from typing import TYPE_CHECKING

from opentelemetry import trace

from ivlia.application.orchestration.graph import AgentGraph, stream_reply
from ivlia.contract.events import EndEvent, ErrorEvent, Event, TokenEvent

if TYPE_CHECKING:
    from collections.abc import AsyncIterator

    from ivlia.domain.agents.state import AgentState

logger = logging.getLogger(__name__)
_tracer = trace.get_tracer(__name__)

# Shown to the user. Details go to the log only.
REPLY_FAILED = "The reply failed. See the log for details."


class Chat:
    def __init__(self, graph: AgentGraph) -> None:
        self._graph = graph

    async def __call__(self, state: AgentState) -> AsyncIterator[Event]:
        """Stream the reply as token events, then an end event.

        If the reply fails, the stream ends with an error event instead.
        """
        # The span is not made current: a generator can be closed in another
        # context, which would break detaching it.
        span = _tracer.start_span("chat")
        started = time.monotonic()
        chunks = 0
        try:
            async for chunk in stream_reply(self._graph, state):
                chunks += 1
                yield TokenEvent(text=chunk)
        except Exception as error:
            logger.exception("Chat reply failed")
            # The type only: an exception message can quote the conversation.
            span.set_status(trace.StatusCode.ERROR, type(error).__name__)
            yield ErrorEvent(message=REPLY_FAILED)
            return
        finally:
            span.end()
        # Metadata only: never the conversation (docs/07).
        duration_ms = round((time.monotonic() - started) * 1000)
        logger.info(
            "Chat reply sent", extra={"chunks": chunks, "duration_ms": duration_ms}
        )
        yield EndEvent()
