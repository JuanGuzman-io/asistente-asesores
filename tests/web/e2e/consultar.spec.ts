// e2e contra el backend real de MDO-0001 en :8000 y la interfaz en vite dev (D5, C-3).
import { expect, test } from "@playwright/test";

test("consulta exitosa muestra respuesta, estado y fuente @S-1.1 @S-2.1", async ({ page }) => {
  await page.goto("/");
  await page.getByLabel("Pregunta").fill("¿Cuál es el monto máximo del Crédito Productivo Impulso?");
  // La petición se retiene hasta ver "Procesando consulta…": así no depende de la velocidad del backend.
  let soltar = () => {};
  const retenida = new Promise<void>((resolve) => (soltar = resolve));
  await page.route("**/api/consultar", async (route) => {
    await retenida;
    await route.continue();
  });
  await page.getByRole("button", { name: "Consultar" }).click();

  await expect(page.getByText("Procesando consulta…")).toBeVisible();
  soltar();
  const resultado = page.getByRole("region", {
    name: "Resultado de la consulta",
  });
  await expect(resultado).toBeVisible();
  await expect(resultado.getByText("Exitosa", { exact: true })).toBeVisible();
  await expect(resultado.getByRole("heading", { name: "Respuesta" })).toBeVisible();
  const fuente = resultado
    .getByRole("listitem")
    .filter({ hasText: "Productos de Crédito > Crédito Productivo Impulso" })
    .first();
  await expect(fuente).toBeVisible();
  await expect(fuente.locator("blockquote")).not.toBeEmpty();
  await expect(page.getByText("Procesando consulta…")).toBeHidden();
});

test("caja vacía: el botón está deshabilitado y no sale ninguna petición @S-1.3", async ({ page }) => {
  let peticiones = 0;
  page.on("request", (request) => {
    if (request.url().endsWith("/api/consultar")) peticiones += 1;
  });
  await page.goto("/");
  await expect(page.getByRole("button", { name: "Consultar" })).toBeDisabled();

  await page.getByLabel("Pregunta").press("Enter");
  // Un viaje de ida y vuelta por la página deja asentado cualquier envío pendiente.
  await page.evaluate(() => new Promise((resolve) => requestAnimationFrame(() => setTimeout(resolve, 100))));
  expect(peticiones).toBe(0);
});

test("error visible con un 422 forzado muestra el mensaje y el código de referencia @S-3.1", async ({
  page,
}) => {
  await page.route("**/api/consultar", (route) =>
    route.fulfill({
      status: 422,
      contentType: "application/problem+json",
      body: JSON.stringify({
        detail: "La pregunta no puede estar vacía.",
        requestId: "abc-123",
        status: 422,
      }),
    }),
  );
  await page.goto("/");
  await page.getByLabel("Pregunta").fill("¿Cuál es el monto máximo del Crédito Productivo Impulso?");
  await page.getByRole("button", { name: "Consultar" }).click();

  const alerta = page.getByRole("alert");
  await expect(alerta).toBeVisible();
  await expect(alerta).toContainText("La pregunta no puede estar vacía.");
  await expect(alerta).toContainText("Código de referencia: abc-123");
});

test("pregunta sin información muestra el estado y no hay fuentes @S-2.2", async ({ page }) => {
  await page.goto("/");
  await page.getByLabel("Pregunta").fill("¿Va a llover mañana en Bogotá?");
  await page.getByRole("button", { name: "Consultar" }).click();

  const resultado = page.getByRole("region", {
    name: "Resultado de la consulta",
  });
  await expect(resultado.getByText("Sin información suficiente")).toBeVisible();
  await expect(resultado.getByText("Sin fuentes")).toBeVisible();
  await expect(resultado.getByText("Exitosa", { exact: true })).toHaveCount(0);
});
