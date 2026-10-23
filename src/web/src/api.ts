// Cliente de la API (D3): traduce cada respuesta del servicio y nunca lanza.
export type Estado = "Exitosa" | "Sin información suficiente" | "Bloqueada por seguridad";

export interface Fuente {
  documento: string;
  seccion: string;
  fragmento: string;
}

export interface Resultado {
  respuesta: string;
  fuentes: Fuente[];
  estado: Estado;
}

export type RespuestaConsulta =
  { tipo: "ok"; resultado: Resultado } | { tipo: "error"; mensaje: string; codigoReferencia?: string };

export interface Opciones {
  signal?: AbortSignal;
}

const TIEMPO_LIMITE_MS = 30_000;
const ESTADOS: readonly string[] = ["Exitosa", "Sin información suficiente", "Bloqueada por seguridad"];

const MENSAJE_GENERICO = "El servicio tuvo un problema. Intenta de nuevo en unos minutos.";
const MENSAJE_SIN_CONEXION = "No se pudo conectar con el servicio. Verifica que esté en ejecución.";
const MENSAJE_TIEMPO_AGOTADO = "El servicio tardó demasiado en responder. Intenta de nuevo.";
const MENSAJE_REVISAR = "Revisa la pregunta e intenta de nuevo.";
const MENSAJE_LARGA = "La pregunta es demasiado larga.";

function esRegistro(valor: unknown): valor is Record<string, unknown> {
  return typeof valor === "object" && valor !== null && !Array.isArray(valor);
}

function esTexto(valor: unknown): valor is string {
  return typeof valor === "string";
}

function esFuente(valor: unknown): valor is Fuente {
  return esRegistro(valor) && esTexto(valor.documento) && esTexto(valor.seccion) && esTexto(valor.fragmento);
}

function esResultado(valor: unknown): valor is Resultado {
  return (
    esRegistro(valor) &&
    esTexto(valor.respuesta) &&
    esTexto(valor.estado) &&
    ESTADOS.includes(valor.estado) &&
    Array.isArray(valor.fuentes) &&
    valor.fuentes.every(esFuente)
  );
}

function error(mensaje: string, codigoReferencia?: string): RespuestaConsulta {
  return codigoReferencia === undefined
    ? { tipo: "error", mensaje }
    : { tipo: "error", mensaje, codigoReferencia };
}

async function leerJson(respuesta: Response): Promise<unknown> {
  try {
    return await respuesta.json();
  } catch {
    return undefined;
  }
}

function mensajeDeEstado(status: number, cuerpo: unknown): string {
  if (status === 413) return MENSAJE_LARGA;
  if (status !== 422) return MENSAJE_GENERICO;
  const detail = esRegistro(cuerpo) ? cuerpo.detail : undefined;
  return esTexto(detail) && detail.trim() !== "" ? detail : MENSAJE_REVISAR;
}

async function traducir(respuesta: Response): Promise<RespuestaConsulta> {
  const cuerpo = await leerJson(respuesta);
  if (respuesta.status === 200) {
    return esResultado(cuerpo) ? { tipo: "ok", resultado: cuerpo } : error(MENSAJE_GENERICO);
  }
  const requestId = esRegistro(cuerpo) && esTexto(cuerpo.requestId) ? cuerpo.requestId : undefined;
  return error(mensajeDeEstado(respuesta.status, cuerpo), requestId);
}

function esTiempoAgotado(causa: unknown): boolean {
  return esRegistro(causa) && (causa.name === "TimeoutError" || causa.name === "AbortError");
}

export async function consultar(pregunta: string, opciones: Opciones = {}): Promise<RespuestaConsulta> {
  const signal = opciones.signal ?? AbortSignal.timeout(TIEMPO_LIMITE_MS);
  try {
    const respuesta = await fetch("/api/consultar", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ pregunta }),
      signal,
    });
    return await traducir(respuesta);
  } catch (causa) {
    return error(esTiempoAgotado(causa) ? MENSAJE_TIEMPO_AGOTADO : MENSAJE_SIN_CONEXION);
  }
}
