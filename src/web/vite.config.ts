import react from "@vitejs/plugin-react";
import { loadEnv } from "vite";
import { defineConfig } from "vitest/config";

// tests/web queda fuera de src/web: sus imports de paquetes se resuelven en src/web/node_modules.
const paquete = (nombre: string) => ({
  find: new RegExp(`^${nombre}(/.*)?$`),
  replacement: `${decodeURIComponent(new URL(`./node_modules/${nombre}`, import.meta.url).pathname)}$1`,
});

const DENEGADOS = [".env", ".env.*", "*.{crt,pem}", "**/.git/**", "**/Data/**"];

export default defineConfig(({ mode }) => {
  const apiUrl = loadEnv(mode, ".", "API_").API_URL ?? "http://127.0.0.1:8000";
  return {
    plugins: [react()],
    server: { fs: { allow: [".", "../../tests/web"], deny: DENEGADOS }, proxy: { "/api": apiUrl } },
    preview: { proxy: { "/api": apiUrl } },
    test: {
      environment: "jsdom",
      alias: [
        "react",
        "react-dom",
        "@testing-library/react",
        "@testing-library/dom",
        "@testing-library/user-event",
      ].map(paquete),
      include: ["src/**/*.test.{ts,tsx}", "../../tests/web/**/*.test.{ts,tsx}"],
      exclude: ["../../tests/web/e2e/**", "node_modules/**"],
    },
  };
});
