// T2 · AC-1, AC-1/C2, AC-1/C3 · FR-2 · D4. Resultado pinta respuesta, estado y fuentes como texto.
// ASSUMPTION: el spec no fija las props; se usa `<Resultado resultado={...} />` (export con nombre)
// con `resultado` del tipo Resultado de api.ts.
import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import type {
  Estado,
  Resultado as DatosResultado,
} from "../../src/web/src/api";
import { Resultado } from "../../src/web/src/Resultado";

const FUENTE = {
  documento: "Productos de Crédito",
  seccion: "Crédito Productivo Impulso",
  fragmento: "Monto hasta 50 millones.",
};
const ESTADOS: Estado[] = [
  "Exitosa",
  "Sin información suficiente",
  "Bloqueada por seguridad",
];

function pintar(parcial: Partial<DatosResultado>) {
  const resultado: DatosResultado = {
    respuesta: "r",
    fuentes: [],
    estado: "Exitosa",
    ...parcial,
  };
  return render(<Resultado resultado={resultado} />);
}

afterEach(cleanup);

describe("Resultado: consulta exitosa (FR-2)", () => {
  it("S-2.1: muestra la respuesta y el estado Exitosa", () => {
    pintar({ respuesta: "El monto máximo es $50.000.000.", fuentes: [FUENTE] });
    expect(screen.getByText("El monto máximo es $50.000.000.")).toBeTruthy();
    expect(screen.getByText("Exitosa")).toBeTruthy();
  });

  it("S-2.1: muestra la fuente como 'documento > sección' con su fragmento", () => {
    pintar({ fuentes: [FUENTE] });
    expect(
      screen.getByText("Productos de Crédito > Crédito Productivo Impulso"),
    ).toBeTruthy();
    expect(screen.getByText(FUENTE.fragmento)).toBeTruthy();
    expect(screen.queryByText("Sin fuentes")).toBeNull();
  });
});

describe("Resultado: estados con su propio rótulo (AC-1/C2)", () => {
  it("S-2.2: sin información suficiente muestra mensaje, 'Sin fuentes' y su rótulo", () => {
    pintar({
      respuesta: "No tengo información suficiente para responder.",
      estado: "Sin información suficiente",
    });
    expect(
      screen.getByText("No tengo información suficiente para responder."),
    ).toBeTruthy();
    expect(screen.getByText("Sin fuentes")).toBeTruthy();
    expect(screen.getByText("Sin información suficiente")).toBeTruthy();
    expect(screen.queryByText("Exitosa")).toBeNull();
  });

  it("S-2.2/C2: el rótulo de Sin información suficiente difiere del de Exitosa", () => {
    const a = pintar({ estado: "Exitosa" });
    const rotuloExitosa = screen.getByText("Exitosa").textContent;
    a.unmount();
    pintar({ estado: "Sin información suficiente" });
    expect(screen.getByText("Sin información suficiente").textContent).not.toBe(
      rotuloExitosa,
    );
  });

  it("S-2.3: Bloqueada por seguridad muestra la respuesta, su rótulo y 'Sin fuentes'", () => {
    pintar({
      respuesta: "Consulta bloqueada.",
      estado: "Bloqueada por seguridad",
    });
    expect(screen.getByText("Consulta bloqueada.")).toBeTruthy();
    expect(screen.getByText("Bloqueada por seguridad")).toBeTruthy();
    expect(screen.getByText("Sin fuentes")).toBeTruthy();
  });

  it("S-2.3/C2: cada estado muestra únicamente su propio rótulo, también sin fuentes", () => {
    for (const estado of ESTADOS) {
      const { unmount } = pintar({ estado });
      expect(screen.getAllByText(estado)).toHaveLength(1);
      for (const otro of ESTADOS.filter((e) => e !== estado))
        expect(screen.queryByText(otro)).toBeNull();
      unmount();
    }
  });
});

describe("Resultado: texto del servicio como texto (AC-1/C3, D4)", () => {
  const HTML = '<b>hola</b> y <a href="https://ejemplo.com">x</a>';

  it("S-2.4: respuesta y fragmento con <b> y <a> aparecen literales", () => {
    pintar({ respuesta: HTML, fuentes: [{ ...FUENTE, fragmento: HTML }] });
    expect(screen.getAllByText(HTML)).toHaveLength(2);
  });

  it("S-2.4/C3: no se crean elementos b ni a", () => {
    const { container } = pintar({
      respuesta: HTML,
      fuentes: [{ ...FUENTE, fragmento: HTML }],
    });
    expect(container.querySelector("b")).toBeNull();
    expect(container.querySelector("a")).toBeNull();
    expect(screen.queryByRole("link")).toBeNull();
  });

  it("S-2.4/C3: documento y sección con HTML tampoco crean elementos", () => {
    const { container } = pintar({
      fuentes: [
        { documento: "<b>D</b>", seccion: '<a href="x">S</a>', fragmento: "f" },
      ],
    });
    expect(container.querySelector("b, a")).toBeNull();
    expect(screen.queryByRole("link")).toBeNull();
  });
});
