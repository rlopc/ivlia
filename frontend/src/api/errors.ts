/** The API could not be used. The message is shown to the user as is. */
export class ApiError extends Error {
  override name = "ApiError";
}

export function describeStatus(status: number): string {
  if (status === 401) {
    return "Your session has ended. Run `ivlia web` to open a new one.";
  }
  return `The API answered with status ${String(status)}.`;
}

export const UNREACHABLE = "Cannot reach the ivlia server. Is it running?";
