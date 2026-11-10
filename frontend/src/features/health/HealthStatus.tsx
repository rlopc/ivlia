import { useQuery } from "@tanstack/react-query";
import { fetchHealth } from "@/api/health";

export function HealthStatus() {
  const { data, error } = useQuery({
    queryKey: ["health"],
    queryFn: ({ signal }) => fetchHealth(signal),
  });
  const label = error
    ? "API unavailable"
    : data
      ? `API ${data.status}`
      : "Checking the API";
  return (
    <p role="status" className="text-sm text-muted-foreground">
      {label}
    </p>
  );
}
