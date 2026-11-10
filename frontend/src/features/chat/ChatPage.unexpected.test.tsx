import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { http, HttpResponse } from "msw";
import { expect, it, vi } from "vitest";
import { renderApp } from "@/test/render";
import { server } from "@/test/server";

// A failure that is not an ApiError, such as a bug, gets a generic message.
vi.mock("@/api/chat", () => ({
  streamChat: () => {
    throw new TypeError("a bug");
  },
}));

it("shows a generic message for an unexpected failure", async () => {
  server.use(
    http.get("/api/health", () => HttpResponse.json({ status: "ok" })),
  );
  renderApp();
  const user = userEvent.setup();
  await user.type(screen.getByRole("textbox", { name: "Message" }), "hello");
  await user.click(screen.getByRole("button", { name: "Send" }));
  expect((await screen.findByRole("alert")).textContent).toBe(
    "The reply failed.",
  );
});
