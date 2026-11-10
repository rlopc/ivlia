import { http, HttpResponse } from "msw";
import { describe, expect, it } from "vitest";
import { server } from "@/test/server";
import { fetchHealth } from "./health";

function answer(response: () => Response) {
  server.use(http.get("/api/health", response));
}

describe("fetchHealth", () => {
  it("returns the status", async () => {
    answer(() => HttpResponse.json({ status: "ok" }));
    expect(await fetchHealth()).toEqual({ status: "ok" });
  });

  it.each([[{}], [{ status: 1 }], [null]])(
    "rejects an invalid body: %j",
    async (body) => {
      answer(() => HttpResponse.json(body));
      await expect(fetchHealth()).rejects.toThrow("invalid health status");
    },
  );

  it("reports an error status", async () => {
    answer(() => new HttpResponse(null, { status: 500 }));
    await expect(fetchHealth()).rejects.toThrow("status 500");
  });

  it("reports an unreachable server", async () => {
    answer(() => HttpResponse.error());
    await expect(fetchHealth()).rejects.toThrow("Cannot reach");
  });

  it("lets a cancellation through", async () => {
    answer(() => HttpResponse.json({ status: "ok" }));
    const controller = new AbortController();
    controller.abort();
    await expect(fetchHealth(controller.signal)).rejects.toThrow(
      expect.objectContaining({ name: "AbortError" }) as Error,
    );
  });
});
