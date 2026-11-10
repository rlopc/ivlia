import { QueryClient } from "@tanstack/react-query";
import { render } from "@testing-library/react";
import { App } from "@/app/App";

/** Render the whole app at `path`, with a fresh query cache and no retries. */
export function renderApp(path = "/") {
  window.history.pushState({}, "", path);
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return render(<App queryClient={queryClient} />);
}
