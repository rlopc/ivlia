import { screen } from "@testing-library/react";
import { http, HttpResponse } from "msw";
import { describe, expect, it } from "vitest";
import { renderApp } from "@/test/render";
import { server } from "@/test/server";

describe("app", () => {
  it("shows the API status", async () => {
    server.use(
      http.get("/api/health", () => HttpResponse.json({ status: "ok" })),
    );
    renderApp();
    expect(screen.getByRole("status").textContent).toBe("Checking the API");
    expect(await screen.findByText("API ok")).toBeDefined();
  });

  it("says when the API is unavailable", async () => {
    server.use(http.get("/api/health", () => HttpResponse.error()));
    renderApp();
    expect(await screen.findByText("API unavailable")).toBeDefined();
  });

  it("shows a not-found page with a way back", async () => {
    server.use(
      http.get("/api/health", () => HttpResponse.json({ status: "ok" })),
    );
    renderApp("/nowhere");
    expect(
      screen.getByRole("heading", { name: "Page not found" }),
    ).toBeDefined();
    expect(
      screen.getByRole("link", { name: "Back to the chat" }),
    ).toBeDefined();
    await screen.findByText("API ok");
  });
});
