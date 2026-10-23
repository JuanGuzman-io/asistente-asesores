// T3 · AC-1, AC-1/C1, AC-2, AC-2/C2 · FR-1, FR-3, FR-4 · NFR-1 · D3. La pantalla consulta y muestra el estado.
// ASSUMPTION: `App` es un export con nombre sin props; el botón se llama "Consultar"; la región de
// estado es role="status" con aria-live="polite" y contiene "Procesando consulta…"; el error es
// role="alert". `EstadoProcesamiento` es interno de App: se observa por su efecto en pantalla
// (procesando = texto de espera; completado = Resultado; error = alert). `fetch` se simula (D5).
import { cleanup, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { App } from "../../src/web/src/App";

const OK = {
  respuesta: "El monto máximo es $50.000.000.",
  fuentes: [
    {
      documento: "Productos de Crédito",
      seccion: "Impulso",
      fragmento: "Hasta 50 millones.",
    },
  ],
  estado: "Exitosa",
};
const json = (cuerpo: unknown, status = 200) =>
  new Response(JSON.stringify(cuerpo), {
    status,
    headers: { "Content-Type": "application/json" },
  });

let pendientes: Array<(r: Response) => void>;
let fetchMock: ReturnType<typeof vi.fn>;

beforeEach(() => {
  pendientes = [];
  fetchMock = vi.fn(() => new Promise<Response>((resolve) => pendientes.push(resolve)));
  vi.stubGlobal("fetch", fetchMock);
});
afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

async function enviar(pregunta = "¿Cuál es el monto?") {
  const user = userEvent.setup();
  render(<App />);
  const campo = screen.getByLabelText("Pregunta");
  if (pregunta !== "") await user.type(campo, pregunta);
  await user.click(screen.getByRole("button", { name: "Consultar" }));
  return { user, campo };
}

describe("App: procesamiento (FR-1)", () => {
  it("S-1.1: muestra 'Procesando consulta…' mientras espera", async () => {
    await enviar();
    expect(await screen.findByText("Procesando consulta…")).toBeTruthy();
    expect(fetchMock).toHaveBeenCalledTimes(1);
  });

  it("S-1.1: al llegar la respuesta pasa a completado y pinta Resultado", async () => {
    await enviar();
    pendientes[0]!(json(OK));
    expect(await screen.findByText(OK.respuesta)).toBeTruthy();
    expect(screen.getByText("Exitosa")).toBeTruthy();
    expect(screen.getByText("Productos de Crédito > Impulso")).toBeTruthy();
    expect(screen.queryByText("Procesando consulta…")).toBeNull();
  });

  it("S-1.2/C1: con la consulta en procesando, el botón no envía otra petición", async () => {
    const { user } = await enviar();
    await screen.findByText("Procesando consulta…");
    await user.click(screen.getByRole("button", { name: "Consultar" }));
    await user.click(screen.getByRole("button", { name: "Consultar" }));
    expect(fetchMock).toHaveBeenCalledTimes(1);
  });

  it("S-1.2/C1: con la consulta en procesando, Enter en el campo no envía otra petición", async () => {
    const { user, campo } = await enviar();
    await screen.findByText("Procesando consulta…");
    await user.type(campo, "{Enter}");
    await user.type(campo, "{Enter}");
    expect(fetchMock).toHaveBeenCalledTimes(1);
  });
});

describe("App: errores y reintento (FR-3, FR-4)", () => {
  const ERROR = { requestId: "abc-123", detail: "interno" };

  it("S-3.1: un 422 se ve con role=alert, su detail y el código de referencia", async () => {
    await enviar("");
    pendientes[0]!(
      json({ detail: "La pregunta no puede estar vacía.", requestId: "abc-123", status: 422 }, 422),
    );
    const alerta = await screen.findByRole("alert");
    expect(alerta.textContent).toContain("La pregunta no puede estar vacía.");
    expect(alerta.textContent).toContain("Código de referencia: abc-123");
    expect(screen.queryByText("Procesando consulta…")).toBeNull();
  });

  it("S-4.1/C2: tras un error la pregunta sigue en el campo, editable, y el botón habilitado", async () => {
    const { user, campo } = await enviar("mi pregunta");
    pendientes[0]!(json(ERROR, 500));
    await screen.findByRole("alert");
    const campoFinal = screen.getByLabelText("Pregunta") as HTMLTextAreaElement | HTMLInputElement;
    expect(campoFinal.value).toBe("mi pregunta");
    expect(campoFinal.disabled).toBe(false);
    expect(campoFinal.readOnly).toBe(false);
    expect((screen.getByRole("button", { name: "Consultar" }) as HTMLButtonElement).disabled).toBe(false);
    await user.type(campo, " más");
    expect((screen.getByLabelText("Pregunta") as HTMLInputElement).value).toBe("mi pregunta más");
  });

  it("S-4.1: un nuevo envío limpia el error anterior y permite una segunda petición", async () => {
    const { user } = await enviar();
    pendientes[0]!(json(ERROR, 500));
    await screen.findByRole("alert");
    await user.click(screen.getByRole("button", { name: "Consultar" }));
    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(2));
    expect(screen.queryByRole("alert")).toBeNull();
    expect(await screen.findByText("Procesando consulta…")).toBeTruthy();
  });

  it("S-4.1: un nuevo envío limpia el resultado anterior", async () => {
    const { user } = await enviar();
    pendientes[0]!(json(OK));
    await screen.findByText(OK.respuesta);
    await user.click(screen.getByRole("button", { name: "Consultar" }));
    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(2));
    expect(screen.queryByText(OK.respuesta)).toBeNull();
    expect(screen.queryByText("Exitosa")).toBeNull();
  });
});

describe("App: accesibilidad (NFR-1)", () => {
  it("NFR-1: el campo tiene la etiqueta 'Pregunta'", () => {
    render(<App />);
    expect(screen.getByLabelText("Pregunta")).toBeTruthy();
  });

  it("NFR-1: la región de estado es aria-live='polite' y anuncia el procesamiento", async () => {
    await enviar();
    await screen.findByText("Procesando consulta…");
    const region = screen.getByRole("status");
    expect(region.getAttribute("aria-live")).toBe("polite");
    expect(region.textContent).toContain("Procesando consulta…");
  });

  it("NFR-1: el resultado se inserta en una región aria-live='polite' que ya existía", async () => {
    await enviar();
    const previas = Array.from(document.querySelectorAll('[aria-live="polite"]'));
    pendientes[0]!(json(OK));
    const resultado = await screen.findByRole("region", { name: "Resultado de la consulta" });
    const contenedor = resultado.parentElement?.closest('[aria-live="polite"]');
    expect(contenedor).toBeTruthy();
    expect(previas).toContain(contenedor);
  });
});
