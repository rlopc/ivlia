import { HttpResponse } from "msw";

/**
 * An SSE response with these `data:` lines. MSW's `sse` handler works only
 * in the browser, so Node tests stream the body themselves.
 */
export function sseResponse(
  data: readonly string[],
): HttpResponse<ReadableStream> {
  const encoder = new TextEncoder();
  const body = new ReadableStream<Uint8Array>({
    start(controller) {
      for (const line of data)
        controller.enqueue(encoder.encode(`data: ${line}\n\n`));
      controller.close();
    },
  });
  return new HttpResponse(body, {
    headers: { "Content-Type": "text/event-stream" },
  });
}

export const HELLO = [
  '{"type":"token","text":"Hello"}',
  '{"type":"token","text":", world!"}',
  '{"type":"end"}',
];
