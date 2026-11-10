import {
  AssistantRuntimeProvider,
  ComposerPrimitive,
  ErrorPrimitive,
  MessagePrimitive,
  ThreadPrimitive,
} from "@assistant-ui/react";
import { Button } from "@/components/ui/button";
import { useChatRuntime } from "./useChatRuntime";

/** The chat, built from assistant-ui's unstyled primitives. */
export function ChatThread() {
  const runtime = useChatRuntime();
  return (
    <AssistantRuntimeProvider runtime={runtime}>
      <ThreadPrimitive.Root className="flex min-h-0 flex-1 flex-col">
        <ThreadPrimitive.Viewport className="flex flex-1 flex-col gap-4 overflow-y-auto p-4">
          <ThreadPrimitive.Messages>
            {({ message }) =>
              message.role === "user" ? <UserMessage /> : <AssistantMessage />
            }
          </ThreadPrimitive.Messages>
        </ThreadPrimitive.Viewport>
        <ComposerPrimitive.Root className="flex gap-2 border-t p-4">
          <ComposerPrimitive.Input
            aria-label="Message"
            placeholder="Ask ivlia"
            className="flex-1 resize-none rounded-lg border bg-background px-3 py-2 text-sm"
          />
          <ComposerPrimitive.Send asChild>
            <Button type="submit">Send</Button>
          </ComposerPrimitive.Send>
        </ComposerPrimitive.Root>
      </ThreadPrimitive.Root>
    </AssistantRuntimeProvider>
  );
}

function UserMessage() {
  return (
    <MessagePrimitive.Root className="self-end rounded-lg bg-muted px-3 py-2">
      <MessagePrimitive.Parts />
    </MessagePrimitive.Root>
  );
}

function AssistantMessage() {
  return (
    <MessagePrimitive.Root className="self-start">
      <MessagePrimitive.Parts />
      <MessagePrimitive.Error>
        <ErrorPrimitive.Root role="alert" className="text-sm text-destructive">
          <ErrorPrimitive.Message />
        </ErrorPrimitive.Root>
      </MessagePrimitive.Error>
    </MessagePrimitive.Root>
  );
}
