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
    <div role="alert">
      <p>{error.mensaje}</p>
      {error.codigoReferencia !== undefined && <p>{`Código de referencia: ${error.codigoReferencia}`}</p>}
    </div>
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
    <main>
      <h1>Asistente para asesores</h1>
      <form onSubmit={enviar}>
        <label>
          Pregunta
          <input value={pregunta} onChange={(e) => setPregunta(e.target.value)} />
        </label>
        <button type="submit" disabled={procesando}>
          Consultar
        </button>
      </form>
      <div role="status" aria-live="polite">
        {procesando && "Procesando consulta…"}
      </div>
      {error && <Alerta error={error} />}
      {resultado && <Resultado resultado={resultado} />}
    </main>
  );
}
