// T5 · AC-1/C4 · S-1.3, S-1.4 · D8, P4. La regla de la pregunta: puntos de código de NFC + trim, entre 1 y 1.000.
// ASSUMPTION: `src/web/src/pregunta.ts` exporta MAXIMO_PREGUNTA, largoPregunta y preguntaValida (D8).
import { describe, expect, it } from "vitest";
import { MAXIMO_PREGUNTA, largoPregunta, preguntaValida } from "../../src/web/src/pregunta";

describe("pregunta (D8, P4)", () => {
  it("MAXIMO_PREGUNTA es 1000", () => {
    expect(MAXIMO_PREGUNTA).toBe(1000);
  });

  it.each([[""], ["  \t\n "], [" "]])("S-1.3: %j tiene largo 0 y no es válida", (texto) => {
    expect(largoPregunta(texto)).toBe(0);
    expect(preguntaValida(texto)).toBe(false);
  });

  it("S-1.4: 1.000 'é' precompuestas son válidas, largo 1000", () => {
    const texto = "é".repeat(1000);
    expect(largoPregunta(texto)).toBe(1000);
    expect(preguntaValida(texto)).toBe(true);
  });

  it("S-1.4: 1.000 'é' descompuestas (e + tilde combinable) cuentan 1 cada una tras NFC", () => {
    const texto = "é".repeat(1000);
    expect(largoPregunta(texto)).toBe(1000);
    expect(preguntaValida(texto)).toBe(true);
  });

  it("S-1.4: 1.000 emojis son válidos, cada uno cuenta 1", () => {
    const texto = "\u{1F600}".repeat(1000);
    expect(largoPregunta(texto)).toBe(1000);
    expect(preguntaValida(texto)).toBe(true);
  });

  it("S-1.4: los espacios a los lados no cuentan", () => {
    const texto = "  " + "a".repeat(1000) + "\n";
    expect(largoPregunta(texto)).toBe(1000);
    expect(preguntaValida(texto)).toBe(true);
  });

  it("S-1.4: 1.001 caracteres no son válidos, largo 1001", () => {
    const texto = "a".repeat(1001);
    expect(largoPregunta(texto)).toBe(1001);
    expect(preguntaValida(texto)).toBe(false);
  });

  it("un solo carácter es válido", () => {
    expect(largoPregunta("a")).toBe(1);
    expect(preguntaValida("a")).toBe(true);
  });
});
