import { describe, expect, it } from "vitest";
import { convertMessage, messageText } from "./useChatRuntime";

describe("chat adapter", () => {
  it("keeps only the text parts of a composer message", () => {
    const content = [
      { type: "text", text: "one" },
      { type: "image", image: "data:," },
      { type: "text", text: "two" },
    ] as const;
    expect(messageText({ content: [...content] })).toBe("one\ntwo");
  });

  it("converts each reply status for assistant-ui", () => {
    const base = { id: "a1", role: "assistant", text: "x" } as const;
    expect(convertMessage({ ...base, status: "running" }).status).toEqual({
      type: "running",
    });
    expect(convertMessage({ ...base, status: "complete" }).status).toEqual({
      type: "complete",
      reason: "stop",
    });
    expect(
      convertMessage({ ...base, status: "error", error: "It broke." }).status,
    ).toEqual({ type: "incomplete", reason: "error", error: "It broke." });
  });

  it("gives user messages no status", () => {
    const message = convertMessage({
      id: "u1",
      role: "user",
      text: "hi",
      status: "complete",
    });
    expect(message).toEqual({
      id: "u1",
      role: "user",
      content: [{ type: "text", text: "hi" }],
    });
  });
});
