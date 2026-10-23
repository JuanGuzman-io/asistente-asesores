// Pantalla de consulta (D3): formulario y EstadoProcesamiento en useState.
import { useState } from "react";
import type { FormEvent } from "react";
import { consultar } from "./api";
import type { Resultado as DatosResultado } from "./api";
import { Resultado } from "./Resultado";

type EstadoProcesamiento = "inactivo" | "procesando" | "completado" | "error";

interface ErrorVisible {
  mensaje: string;
  codigoReferencia?: string;
}

function Alerta({ error }: { error: ErrorVisible }) {
  return (
    <div role="alert" className="alerta">
      <p>{error.mensaje}</p>
      {error.codigoReferencia !== undefined && (
        <p className="referencia">{`Código de referencia: ${error.codigoReferencia}`}</p>
      )}
    </div>
  );
}

// Marcador visual mientras llega la respuesta; el anuncio lo hace la región de estado.
function Esqueleto() {
  return (
    <div className="esqueleto panel" aria-hidden="true">
      <span />
      <span />
      <span />
      <span />
    </div>
  );
}

function Encabezado() {
  return (
    <header className="encabezado">
      <h1>Asistente para asesores</h1>
      <p>Respuestas basadas en los documentos oficiales, con sus fuentes.</p>
    </header>
  );
}

interface PropsFormulario {
  pregunta: string;
  onCambio: (pregunta: string) => void;
  onEnviar: (evento: FormEvent) => void;
  procesando: boolean;
}

function Formulario({ pregunta, onCambio, onEnviar, procesando }: PropsFormulario) {
  return (
    <form onSubmit={onEnviar} className="formulario panel">
      <label htmlFor="pregunta">Pregunta</label>
      <input
        id="pregunta"
        aria-describedby="pregunta-ayuda"
        autoComplete="off"
        value={pregunta}
        onChange={(e) => onCambio(e.target.value)}
      />
      <button type="submit" disabled={procesando}>
        Consultar
      </button>
      <p id="pregunta-ayuda" className="ayuda">
        Por ejemplo: ¿Cuál es el monto máximo del Crédito Productivo Impulso?
      </p>
    </form>
  );
}

export function App() {
  const [pregunta, setPregunta] = useState("");
  const [estado, setEstado] = useState<EstadoProcesamiento>("inactivo");
  const [resultado, setResultado] = useState<DatosResultado | undefined>();
  const [error, setError] = useState<ErrorVisible | undefined>();

  async function enviar(evento: FormEvent) {
    evento.preventDefault();
    if (estado === "procesando") return;
    setEstado("procesando");
    setResultado(undefined);
    setError(undefined);
    const respuesta = await consultar(pregunta);
    if (respuesta.tipo === "ok") {
      setResultado(respuesta.resultado);
      setEstado("completado");
    } else {
      setError(respuesta);
      setEstado("error");
    }
  }

  const procesando = estado === "procesando";
  return (
    <main className="pagina">
      <Encabezado />
      <Formulario pregunta={pregunta} onCambio={setPregunta} onEnviar={enviar} procesando={procesando} />
      <div role="status" aria-live="polite" className="estado-proceso">
        {procesando && "Procesando consulta…"}
      </div>
      {procesando && <Esqueleto />}
      {error && <Alerta error={error} />}
      {/* Siempre montada: los lectores de pantalla anuncian el resultado al insertarse en ella. */}
      <div aria-live="polite">{resultado && <Resultado resultado={resultado} />}</div>
    </main>
  );
}
