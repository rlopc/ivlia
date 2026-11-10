import { http, HttpResponse } from "msw";
import { describe, expect, it, vi } from "vitest";
import type { ApiEvent } from "@/contract/events";
import { server } from "@/test/server";
import { HELLO, sseResponse } from "@/test/sse";
import { streamChat } from "./chat";
import { ApiError } from "./errors";

async function collect(stream: AsyncIterable<ApiEvent>): Promise<ApiEvent[]> {
  const events: ApiEvent[] = [];
  for await (const event of stream) events.push(event);
  return events;
}

function answer(response: () => Response) {
  server.use(http.post("/api/chat", response));
}

describe("streamChat", () => {
  it("sends the message and yields the events", async () => {
    let body: unknown;
    server.use(
      http.post("/api/chat", async ({ request }) => {
        body = await request.json();
        return sseResponse(HELLO);
      }),
    );
    expect(await collect(streamChat("hi"))).toEqual([
      { type: "token", text: "Hello" },
      { type: "token", text: ", world!" },
      { type: "end" },
    ]);
    expect(body).toEqual({ message: "hi" });
  });

  it("skips and logs unknown event types, without their content", async () => {
    const warn = vi.spyOn(console, "warn").mockImplementation(() => undefined);
    answer(() =>
      sseResponse(['{"type":"future","content":"secret"}', '{"type":"end"}']),
    );
    expect(await collect(streamChat("hi"))).toEqual([{ type: "end" }]);
    expect(warn).toHaveBeenCalledExactlyOnceWith(
      "Ignored an event of unknown type",
    );
  });

  it.each([
    ['{"type":"token"}', "missing field"],
    ['{"text":"no type"}', "missing type"],
    ["not json", "not JSON"],
  ])("rejects an invalid event: %s (%s)", async (data) => {
    answer(() => sseResponse([data]));
    await expect(collect(streamChat("hi"))).rejects.toThrow("invalid event");
  });

  it.each([
    [401, "Run `ivlia web`"],
    [500, "status 500"],
  ])("reports status %i", async (status, message) => {
    answer(() => HttpResponse.json({ detail: "x" }, { status }));
    await expect(collect(streamChat("hi"))).rejects.toThrow(message);
  });

  it("reports an unreachable server", async () => {
    answer(() => HttpResponse.error());
    await expect(collect(streamChat("hi"))).rejects.toThrow(ApiError);
  });

  it("rejects a response without a content type", async () => {
    const empty = new ReadableStream({
      start(controller) {
        controller.close();
      },
    });
    answer(() => new HttpResponse(empty, { status: 200 }));
    await expect(collect(streamChat("hi"))).rejects.toThrow(
      "invalid event stream",
    );
  });

  it("rejects a response that is not an event stream", async () => {
    answer(() => HttpResponse.json({ type: "end" }));
    await expect(collect(streamChat("hi"))).rejects.toThrow(
      "invalid event stream",
    );
  });

  it("lets a cancellation through", async () => {
    answer(() => sseResponse(HELLO));
    const controller = new AbortController();
    controller.abort();
    await expect(collect(streamChat("hi", controller.signal))).rejects.toThrow(
      expect.objectContaining({ name: "AbortError" }) as Error,
    );
  });
});
