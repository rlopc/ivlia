import { randomBytes } from "node:crypto";
import { mkdtempSync } from "node:fs";
import { tmpdir } from "node:os";
import path from "node:path";
import { defineConfig, devices } from "@playwright/test";

// The built SPA served by FastAPI, as in use, on its own port and folder, so
// the dev installation's data is never touched. The config also runs in each
// worker: the values are set once and the workers inherit them.
const port = 8767;
const origin = `http://127.0.0.1:${String(port)}`;
process.env.IVLIA_E2E_TOKEN ??= randomBytes(32).toString("base64url");
process.env.IVLIA_E2E_HOME ??= mkdtempSync(path.join(tmpdir(), "ivlia-e2e-"));

export default defineConfig({
  testDir: "e2e",
  globalTeardown: "./e2e/teardown.ts",
  forbidOnly: Boolean(process.env.CI),
  use: { baseURL: origin, trace: "retain-on-failure" },
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
  webServer: {
    command: "uv run --locked --project ../backend ivlia-server",
    url: `${origin}/api/health`,
    reuseExistingServer: false,
    env: {
      IVLIA_ENV: "dev",
      IVLIA_HOME: process.env.IVLIA_E2E_HOME,
      IVLIA_PORT: String(port),
      IVLIA_API_TOKEN: process.env.IVLIA_E2E_TOKEN,
      // One-time links point at the web origin: here, the server itself.
      IVLIA_DEV_ORIGIN: origin,
    },
  },
});
