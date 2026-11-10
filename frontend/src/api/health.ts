import { ApiError, UNREACHABLE, describeStatus } from "./errors";

const INVALID = "The API sent an invalid health status.";

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
  let body: unknown;
  try {
    body = await response.json();
  } catch {
    throw new ApiError(INVALID);
  }
  if (
    typeof body !== "object" ||
    body === null ||
    !("status" in body) ||
    typeof body.status !== "string"
  ) {
    throw new ApiError(INVALID);
  }
  return { status: body.status };
}
