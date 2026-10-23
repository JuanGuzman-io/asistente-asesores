// T1 · AC-2, AC-2/C1 · FR-3 · D3. Cliente de la API con `fetch` simulado (D5); sin red real.
import { afterEach, describe, expect, it, vi } from "vitest";
import { consultar } from "../../src/web/src/api";

const GENERICO = "El servicio tuvo un problema. Intenta de nuevo en unos minutos.";
const SIN_CONEXION = "No se pudo conectar con el servicio. Verifica que esté en ejecución.";
const TIEMPO_AGOTADO = "El servicio tardó demasiado en responder. Intenta de nuevo.";

const FUENTE = { documento: "Productos de Crédito", seccion: "Crédito Productivo Impulso", fragmento: "…" };

function problema(status: number, cuerpo: Record<string, unknown>): Response {
  return new Response(JSON.stringify(cuerpo), {
    status,
    headers: { "Content-Type": "application/problem+json" },
  });
}

function stubFetch(impl: (input: RequestInfo | URL, init?: RequestInit) => Promise<Response>) {
  const fn = vi.fn(impl);
  vi.stubGlobal("fetch", fn);
  return fn;
}

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("consultar: respuesta válida (D3)", () => {
  it("S-2.1 base: 200 válido devuelve ok con respuesta, fuentes y estado", async () => {
    const cuerpo = { respuesta: "El monto máximo es $50.000.000.", fuentes: [FUENTE], estado: "Exitosa" };
    const fn = stubFetch(async () => new Response(JSON.stringify(cuerpo), { status: 200, headers: { "Content-Type": "application/json" } }));
    const r = await consultar("¿Cuál es el monto máximo?");
    expect(r).toEqual({ tipo: "ok", resultado: cuerpo });
    expect(String(fn.mock.calls[0]?.[0])).toBe("/api/consultar");
    expect(fn.mock.calls[0]?.[1]?.method).toBe("POST");
    expect(JSON.parse(String(fn.mock.calls[0]?.[1]?.body))).toEqual({ pregunta: "¿Cuál es el monto máximo?" });
  });

  it.each(["Sin información suficiente", "Bloqueada por seguridad"])("D3: acepta el estado %s", async (estado) => {
    const cuerpo = { respuesta: "x", fuentes: [], estado };
    stubFetch(async () => new Response(JSON.stringify(cuerpo), { status: 200, headers: { "Content-Type": "application/json" } }));
    expect(await consultar("p")).toEqual({ tipo: "ok", resultado: cuerpo });
  });
});

describe("consultar: errores del servicio (FR-3)", () => {
  it("S-3.1: 422 problem+json usa el detail y el requestId como código de referencia", async () => {
    stubFetch(async () => problema(422, { detail: "La pregunta no puede estar vacía.", requestId: "abc-123", status: 422 }));
    expect(await consultar("")).toEqual({
      tipo: "error",
      mensaje: "La pregunta no puede estar vacía.",
      codigoReferencia: "abc-123",
    });
  });

  it("S-3.1 (tabla FR-3): 422 sin detail usa el mensaje de revisión", async () => {
    stubFetch(async () => problema(422, { requestId: "r-1" }));
    expect(await consultar("p")).toEqual({
      tipo: "error",
      mensaje: "Revisa la pregunta e intenta de nuevo.",
      codigoReferencia: "r-1",
    });
  });

  it("S-3.1 (tabla FR-3): 413 dice que la pregunta es demasiado larga", async () => {
    stubFetch(async () => problema(413, { requestId: "r-2" }));
    const r = await consultar("p");
    expect(r).toMatchObject({ tipo: "error", mensaje: "La pregunta es demasiado larga." });
  });

  it("S-3.2: 500 problem+json da el mensaje genérico y el código de referencia", async () => {
    stubFetch(async () => problema(500, { detail: "boom interno", requestId: "srv-9" }));
    expect(await consultar("p")).toEqual({ tipo: "error", mensaje: GENERICO, codigoReferencia: "srv-9" });
  });

  it.each([415, 503, 404])("S-3.2 (tabla FR-3): el código %i da el mensaje genérico", async (status) => {
    stubFetch(async () => problema(status, { requestId: "r-3" }));
    expect(await consultar("p")).toMatchObject({ tipo: "error", mensaje: GENERICO });
  });
});

describe("consultar: sin conexión y tiempo agotado (S-3.3)", () => {
  it("S-3.3: falla de red da el mensaje de conexión, sin código de referencia", async () => {
    stubFetch(async () => {
      throw new TypeError("Failed to fetch");
    });
    const r = await consultar("p");
    expect(r).toEqual({ tipo: "error", mensaje: SIN_CONEXION });
    expect(r).not.toHaveProperty("codigoReferencia");
  });

  it("S-3.3: sin respuesta dentro del tiempo límite inyectado da el mensaje de tiempo agotado", async () => {
    const fn = stubFetch(
      (_input, init) =>
        new Promise<Response>((_resolve, reject) => {
          init?.signal?.addEventListener("abort", () => reject(init.signal?.reason));
        }),
    );
    const r = await consultar("p", { signal: AbortSignal.timeout(20) });
    expect(fn).toHaveBeenCalledOnce();
    expect(r).toEqual({ tipo: "error", mensaje: TIEMPO_AGOTADO });
    expect(r).not.toHaveProperty("codigoReferencia");
  });
});

describe("consultar: sin detalles técnicos (S-3.4, S-3.4/C1, AC-2/C1)", () => {
  const SECRETOS = [
    "Traceback",
    "/usr/lib/python3/site-packages",
    "<html>",
    "stack trace at line 42",
    "NullPointerException",
  ];

  it("S-3.4: 500 con cuerpo HTML da el mensaje genérico sin el cuerpo", async () => {
    stubFetch(
      async () =>
        new Response("<html><body><pre>Traceback /usr/lib/python3/site-packages NullPointerException</pre></body></html>", {
          status: 500,
          headers: { "Content-Type": "text/html" },
        }),
    );
    const r = await consultar("p");
    expect(r).toEqual({ tipo: "error", mensaje: GENERICO });
    const serializado = JSON.stringify(r);
    for (const s of SECRETOS) expect(serializado).not.toContain(s);
  });

  it("S-3.4/C1: 500 con texto plano da el mensaje genérico sin el cuerpo", async () => {
    stubFetch(async () => new Response("Internal error: stack trace at line 42 in /srv/app/main.py", { status: 500, headers: { "Content-Type": "text/plain" } }));
    const r = await consultar("p");
    expect(r).toEqual({ tipo: "error", mensaje: GENERICO });
    const serializado = JSON.stringify(r);
    expect(serializado).not.toContain("stack trace");
    expect(serializado).not.toContain("/srv/app");
  });

  it("S-3.4: 200 con estado fuera de los tres da el mensaje genérico sin nombres de campos ni valores", async () => {
    stubFetch(
      async () =>
        new Response(JSON.stringify({ respuesta: "texto-secreto", fuentes: [], estado: "Estado inventado" }), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        }),
    );
    const r = await consultar("p");
    expect(r).toEqual({ tipo: "error", mensaje: GENERICO });
    const serializado = JSON.stringify(r);
    for (const s of ["texto-secreto", "Estado inventado", "estado", "respuesta", "fuentes"]) {
      expect(serializado).not.toContain(s);
    }
  });

  it("S-3.4: 200 con fuentes que no cumplen el contrato da el mensaje genérico", async () => {
    stubFetch(
      async () =>
        new Response(JSON.stringify({ respuesta: "x", fuentes: [{ documento: "a" }], estado: "Exitosa" }), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        }),
    );
    expect(await consultar("p")).toEqual({ tipo: "error", mensaje: GENERICO });
  });

  it("S-3.4: 200 con cuerpo que no es JSON da el mensaje genérico", async () => {
    stubFetch(async () => new Response("<html>ok</html>", { status: 200, headers: { "Content-Type": "text/html" } }));
    expect(await consultar("p")).toEqual({ tipo: "error", mensaje: GENERICO });
  });

  it("S-3.4/C1: un 500 problem+json no filtra su detail ni otros campos", async () => {
    stubFetch(async () => problema(500, { detail: "Traceback en /srv/app/x.py", requestId: "k-1", trace: "t" }));
    const r = await consultar("p");
    expect(r).toEqual({ tipo: "error", mensaje: GENERICO, codigoReferencia: "k-1" });
    expect(JSON.stringify(r)).not.toContain("Traceback");
  });
});

describe("consultar: nunca lanza (D3)", () => {
  it("D3: un error inesperado de fetch se devuelve como resultado de error", async () => {
    stubFetch(async () => {
      throw new Error("kaboom con /ruta/interna");
    });
    const r = await consultar("p");
    expect(r.tipo).toBe("error");
    expect(JSON.stringify(r)).not.toContain("kaboom");
    expect(JSON.stringify(r)).not.toContain("/ruta/interna");
  });
});
