import path from "node:path";
import tailwindcss from "@tailwindcss/vite";
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

const apiPort = process.env.IVLIA_PORT ?? "8766";

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: { "@": path.resolve(import.meta.dirname, "src") },
  },
  server: {
    // The dev origin the API allows (`dev_origin`): http://localhost:5173.
    host: "localhost",
    port: 5173,
    strictPort: true,
    proxy: {
      // changeOrigin sends the API's own Host, which its allowlist accepts;
      // Origin stays the dev origin. The session cookie is set for localhost.
      "/api": { target: `http://127.0.0.1:${apiPort}`, changeOrigin: true },
    },
  },
  build: {
    // FastAPI serves the built SPA from the package (ivlia.api.spa).
    outDir: path.resolve(
      import.meta.dirname,
      "../backend/src/ivlia/api/static",
    ),
    emptyOutDir: true,
  },
});
