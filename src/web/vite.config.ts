import react from "@vitejs/plugin-react";
import { loadEnv } from "vite";
import { defineConfig } from "vitest/config";

const DENEGADOS = [".env", ".env.*", "*.{crt,pem}", "**/.git/**", "**/Data/**"];

export default defineConfig(({ mode }) => {
  const apiUrl = loadEnv(mode, ".", "API_").API_URL ?? "http://127.0.0.1:8000";
  return {
    plugins: [react()],
    server: { fs: { allow: [".", "../../tests/web"], deny: DENEGADOS }, proxy: { "/api": apiUrl } },
    preview: { proxy: { "/api": apiUrl } },
    test: {
      environment: "jsdom",
      include: ["src/**/*.test.{ts,tsx}", "../../tests/web/**/*.test.{ts,tsx}"],
      exclude: ["../../tests/web/e2e/**", "node_modules/**"],
    },
  };
});
