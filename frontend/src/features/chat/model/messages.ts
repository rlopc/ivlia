import type { ApiEvent } from "@/contract/events";

export type ChatMessage = {
  readonly id: string;
  readonly role: "user" | "assistant";
  readonly text: string;
} & (
  | { readonly status: "running" | "complete" }
  | { readonly status: "error"; readonly error: string }
);

export function userMessage(id: string, text: string): ChatMessage {
  return { id, role: "user", text, status: "complete" };
}

/** An empty assistant message that the reply's events fill in. */
export function pendingReply(id: string): ChatMessage {
  return { id, role: "assistant", text: "", status: "running" };
}

export function applyEvent(message: ChatMessage, event: ApiEvent): ChatMessage {
  switch (event.type) {
    case "token":
      return { ...message, text: message.text + event.text };
    case "end":
      return { ...message, status: "complete" };
    case "error":
      return failReply(message, event.message);
  }
  // No default: TypeScript fails to compile if an event type is not handled.
}

export function failReply(message: ChatMessage, error: string): ChatMessage {
  return { ...message, status: "error", error };
}

/** A reply whose stream ended without `end` or `error` is incomplete. */
export function finishReply(message: ChatMessage): ChatMessage {
  return message.status === "running"
    ? failReply(message, "The answer ended before it was complete.")
    : message;
}
