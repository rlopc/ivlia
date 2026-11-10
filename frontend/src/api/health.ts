import { ApiError, UNREACHABLE, describeStatus } from "./errors";

export interface Health {
  status: string;
}

export async function fetchHealth(signal?: AbortSignal): Promise<Health> {
  let response: Response;
  try {
    response = await fetch("/api/health", { signal: signal ?? null });
  } catch (error) {
    if (signal?.aborted) throw error;
    throw new ApiError(UNREACHABLE);
  }
  if (!response.ok) throw new ApiError(describeStatus(response.status));
  const body: unknown = await response.json();
  if (
    typeof body !== "object" ||
    body === null ||
    !("status" in body) ||
    typeof body.status !== "string"
  ) {
    throw new ApiError("The API sent an invalid health status.");
  }
  return { status: body.status };
}
