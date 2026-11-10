import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Route, Routes } from "react-router";
import { ChatPage } from "@/features/chat/ChatPage";
import { HealthStatus } from "@/features/health/HealthStatus";
import { NotFoundPage } from "./NotFoundPage";

export function App({ queryClient }: { queryClient: QueryClient }) {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <div className="flex h-dvh flex-col">
          <header className="flex items-center justify-between border-b p-4">
            <h1 className="text-lg font-semibold">ivlia</h1>
            <HealthStatus />
          </header>
          <Routes>
            <Route path="/" element={<ChatPage />} />
            <Route path="*" element={<NotFoundPage />} />
          </Routes>
        </div>
      </BrowserRouter>
    </QueryClientProvider>
  );
}
