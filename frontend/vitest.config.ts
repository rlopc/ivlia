import { defineConfig, mergeConfig } from "vitest/config";
import viteConfig from "./vite.config.ts";

export default mergeConfig(
  viteConfig,
  defineConfig({
    test: {
      environment: "jsdom",
      include: ["src/**/*.test.{ts,tsx}"],
      setupFiles: ["src/test/setup.ts"],
      coverage: {
        provider: "v8",
        include: ["src/**/*.{ts,tsx}"],
        exclude: [
          "src/**/*.test.{ts,tsx}",
          "src/test/**",
          // Generated: the contract by our script, ui/ by the shadcn CLI.
          "src/contract/**",
          "src/components/ui/**",
          // The entry point only mounts the app; the end-to-end test runs it.
          "src/app/main.tsx",
        ],
        thresholds: {
          lines: 95,
          functions: 95,
          branches: 95,
          statements: 95,
          "src/features/*/model/**": { 100: true },
        },
      },
    },
  }),
);
