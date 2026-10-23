// e2e (D5): arranca solo la interfaz con `vite dev`; el backend real de MDO-0001 ya debe correr en :8000.
import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
  testDir: "../../tests/web/e2e",
  reporter: "list",
  // El cliente espera hasta 30 s al backend real.
  timeout: 60_000,
  expect: { timeout: 35_000 },
  use: { baseURL: "http://127.0.0.1:5173" },
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
  webServer: {
    command: "npm run dev -- --host 127.0.0.1 --port 5173 --strictPort",
    url: "http://127.0.0.1:5173",
    reuseExistingServer: true,
  },
});
