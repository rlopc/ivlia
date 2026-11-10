import { EventSourceParserStream } from "eventsource-parser/stream";
import type { ApiEvent } from "@/contract/events";
import validateEvent from "@/contract/validate-event.js";
import { ApiError, UNREACHABLE, describeStatus } from "./errors";

/**
 * Send a message and yield the reply's events as they arrive.
 *
 * Unknown event types are skipped (tolerant reader), so an older web keeps
 * working with a newer API. Any other invalid event is an error.
 */
export async function* streamChat(
  message: string,
  signal?: AbortSignal,
): AsyncGenerator<ApiEvent> {
  let response: Response;
  try {
    response = await fetch("/api/chat", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Accept: "text/event-stream",
      },
      body: JSON.stringify({ message }),
      signal: signal ?? null,
    });
  } catch (error) {
    if (signal?.aborted) throw error;
    throw new ApiError(UNREACHABLE);
  }
  if (!response.ok) throw new ApiError(describeStatus(response.status));
  const contentType = response.headers.get("Content-Type") ?? "";
  if (!contentType.startsWith("text/event-stream") || response.body === null) {
    throw new ApiError("The API sent an invalid event stream.");
  }

  const reader = response.body
    .pipeThrough(new TextDecoderStream())
    .pipeThrough(new EventSourceParserStream())
    .getReader();
  try {
    for (;;) {
      const { done, value } = await read(reader, signal);
      if (done) return;
      const event = parseEvent(value.data);
      if (event !== null) yield event;
    }
  } finally {
    // Also when the caller stops early: close the response, not just the
    // reader. On a stream that already failed, cancel rejects with that same
    // error, which must not replace the one being thrown.
    await reader.cancel().catch(() => undefined);
  }
}

async function read<T>(
  reader: ReadableStreamDefaultReader<T>,
  signal: AbortSignal | undefined,
): Promise<ReadableStreamReadResult<T>> {
  try {
    return await reader.read();
  } catch (error) {
    if (signal?.aborted) throw error;
    throw new ApiError("The connection to the ivlia server failed.");
  }
}

function parseEvent(data: string): ApiEvent | null {
  let value: unknown;
  try {
    value = JSON.parse(data);
  } catch {
    throw new ApiError("The API sent an invalid event.");
  }
  if (validateEvent(value)) return value;
  const error = validateEvent.errors?.[0];
  if (error?.keyword === "discriminator" && error.params.error === "mapping") {
    // Type only: the rest of the event may carry content.
    console.warn("Ignored an event of unknown type");
    return null;
  }
  throw new ApiError("The API sent an invalid event.");
}
