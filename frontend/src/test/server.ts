import { setupServer } from "msw/node";

/** The fake API. Each test adds the handlers it needs. */
export const server = setupServer();
