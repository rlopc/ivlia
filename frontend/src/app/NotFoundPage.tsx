import { Link } from "react-router";

export function NotFoundPage() {
  return (
    <main className="p-4">
      <h2 className="text-lg font-medium">Page not found</h2>
      <Link to="/" className="underline">
        Back to the chat
      </Link>
    </main>
  );
}
