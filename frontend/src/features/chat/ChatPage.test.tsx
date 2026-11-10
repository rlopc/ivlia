import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { http, HttpResponse } from "msw";
import { describe, expect, it } from "vitest";
import { renderApp } from "@/test/render";
import { server } from "@/test/server";
import { HELLO, sseResponse } from "@/test/sse";

function api(chat: () => Response) {
  server.use(
    http.get("/api/health", () => HttpResponse.json({ status: "ok" })),
    http.post("/api/chat", chat),
  );
}

async function send(text: string) {
  const user = userEvent.setup();
  await user.type(screen.getByRole("textbox", { name: "Message" }), text);
  await user.click(screen.getByRole("button", { name: "Send" }));
}

describe("chat page", () => {
  it("shows the message and the streamed answer", async () => {
    api(() => sseResponse(HELLO));
    renderApp();
    await send("hello");
    expect(await screen.findByText("Hello, world!")).toBeDefined();
    expect(screen.getByText("hello")).toBeDefined();
  });

  it("shows an error event as an alert", async () => {
    api(() =>
      sseResponse([
        '{"type":"token","text":"Hel"}',
        '{"type":"error","message":"The reply failed."}',
      ]),
    );
    renderApp();
    await send("hello");
    expect((await screen.findByRole("alert")).textContent).toBe(
      "The reply failed.",
    );
  });

  it("shows why the API cannot be used", async () => {
    api(() => HttpResponse.json({ detail: "x" }, { status: 401 }));
    renderApp();
    await send("hello");
    expect((await screen.findByRole("alert")).textContent).toContain(
      "Run `ivlia web`",
    );
  });

  it("reports an answer that ends early", async () => {
    api(() => sseResponse(['{"type":"token","text":"Hel"}']));
    renderApp();
    await send("hello");
    expect((await screen.findByRole("alert")).textContent).toBe(
      "The answer ended before it was complete.",
    );
  });
});
