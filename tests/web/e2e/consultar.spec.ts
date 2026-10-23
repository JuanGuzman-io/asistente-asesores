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

test("pregunta vacía muestra un error con código de referencia @S-3.1", async ({ page }) => {
  // El campo no tiene `required` ni el formulario bloquea el envío: el clic con el campo vacío llega al backend.
  await page.goto("/");
  const respuesta = page.waitForResponse((r) => r.url().endsWith("/api/consultar"));
  await page.getByRole("button", { name: "Consultar" }).click();
  expect((await respuesta).status()).toBe(422);

  const alerta = page.getByRole("alert");
  await expect(alerta).toBeVisible();
  await expect(alerta).toContainText(/Código de referencia: \S+/);
  await expect(alerta).not.toContainText("El servicio tuvo un problema. Intenta de nuevo en unos minutos.");
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
