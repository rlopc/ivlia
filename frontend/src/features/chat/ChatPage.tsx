import { ChatThread } from "./adapter/ChatThread";

export function ChatPage() {
  return (
    <main className="flex min-h-0 flex-1 flex-col">
      <ChatThread />
    </main>
  );
}
