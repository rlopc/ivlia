import {
  useExternalStoreRuntime,
  type AppendMessage,
  type ThreadMessageLike,
} from "@assistant-ui/react";
import { useState } from "react";
import { streamChat } from "@/api/chat";
import { ApiError } from "@/api/errors";
import {
  applyEvent,
  failReply,
  finishReply,
  pendingReply,
  userMessage,
  type ChatMessage,
} from "../model/messages";

/** assistant-ui's runtime over ivlia's own chat state and API. */
export function useChatRuntime() {
  const [messages, setMessages] = useState<readonly ChatMessage[]>([]);
  const [isRunning, setIsRunning] = useState(false);

  async function onNew(message: AppendMessage): Promise<void> {
    const text = messageText(message);
    const replyId = crypto.randomUUID();
    const updateReply = (change: (reply: ChatMessage) => ChatMessage) => {
      setMessages((current) =>
        current.map((m) => (m.id === replyId ? change(m) : m)),
      );
    };

    setMessages((current) => [
      ...current,
      userMessage(crypto.randomUUID(), text),
      pendingReply(replyId),
    ]);
    setIsRunning(true);
    try {
      for await (const event of streamChat(text)) {
        updateReply((reply) => applyEvent(reply, event));
      }
      updateReply(finishReply);
    } catch (error) {
      const reason =
        error instanceof ApiError ? error.message : "The reply failed.";
      updateReply((reply) => failReply(reply, reason));
    } finally {
      setIsRunning(false);
    }
  }

  return useExternalStoreRuntime({
    messages,
    isRunning,
    onNew,
    convertMessage,
  });
}

/** The text of a message from the composer, which sends only text parts. */
export function messageText(message: Pick<AppendMessage, "content">): string {
  return message.content
    .flatMap((part) => (part.type === "text" ? [part.text] : []))
    .join("\n");
}

export function convertMessage(message: ChatMessage): ThreadMessageLike {
  const content = [{ type: "text" as const, text: message.text }];
  if (message.role === "user") {
    return { id: message.id, role: "user", content };
  }
  return {
    id: message.id,
    role: "assistant",
    content,
    status: replyStatus(message),
  };
}

function replyStatus(message: ChatMessage): ThreadMessageLike["status"] {
  switch (message.status) {
    case "running":
      return { type: "running" };
    case "complete":
      return { type: "complete", reason: "stop" };
    case "error":
      return { type: "incomplete", reason: "error", error: message.error };
  }
}
