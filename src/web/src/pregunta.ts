// Regla de la pregunta (D8): mismo criterio que el backend (puntos de código tras NFC y trim, entre 1 y 1.000).
export const MAXIMO_PREGUNTA = 1000;

export function largoPregunta(texto: string): number {
  return [...texto.normalize("NFC").trim()].length;
}

export function preguntaValida(texto: string): boolean {
  const largo = largoPregunta(texto);
  return largo >= 1 && largo <= MAXIMO_PREGUNTA;
}
