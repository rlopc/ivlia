import { describe, expect, it } from "vitest";
import {
  applyEvent,
  failReply,
  finishReply,
  pendingReply,
  userMessage,
} from "./messages";

describe("chat messages", () => {
  it("creates a complete user message", () => {
    expect(userMessage("u1", "hi")).toEqual({
      id: "u1",
      role: "user",
      text: "hi",
      status: "complete",
    });
  });

  it("fills a reply with tokens and completes it on end", () => {
    let reply = pendingReply("a1");
    expect(reply.status).toBe("running");
    reply = applyEvent(reply, { type: "token", text: "Hello" });
    reply = applyEvent(reply, { type: "token", text: ", world!" });
    reply = applyEvent(reply, { type: "end" });
    expect(reply).toEqual({
      id: "a1",
      role: "assistant",
      text: "Hello, world!",
      status: "complete",
    });
  });

  it("fails a reply on an error event, keeping its text", () => {
    const reply = applyEvent(
      applyEvent(pendingReply("a1"), { type: "token", text: "Hel" }),
      { type: "error", message: "It broke." },
    );
    expect(reply).toMatchObject({
      text: "Hel",
      status: "error",
      error: "It broke.",
    });
  });

  it("fails a reply whose stream ended early", () => {
    expect(finishReply(pendingReply("a1"))).toMatchObject({
      status: "error",
      error: "The answer ended before it was complete.",
    });
  });

  it("leaves a finished reply as it is", () => {
    const done = applyEvent(pendingReply("a1"), { type: "end" });
    const failed = failReply(pendingReply("a2"), "x");
    expect(finishReply(done)).toBe(done);
    expect(finishReply(failed)).toBe(failed);
  });
});
