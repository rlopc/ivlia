import { rm } from "node:fs/promises";

/** Removes the run's temporary installation folder (see playwright.config.ts). */
export default async function teardown(): Promise<void> {
  const home = process.env.IVLIA_E2E_HOME;
  if (home !== undefined) await rm(home, { recursive: true, force: true });
}
