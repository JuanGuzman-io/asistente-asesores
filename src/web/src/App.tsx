// Pantalla de W Connect (D3, mock de la spec C-5): formulario y EstadoProcesamiento en useState.
// Antes de la primera consulta, orbe, saludo y caja centrados; después, la conversación arriba y la caja abajo.
// Solo se muestra la consulta en curso: un envío nuevo reemplaza la anterior (sin historial).
import { Plus, WarningCircle } from "@phosphor-icons/react";
import { useEffect, useRef, useState } from "react";
import type { FormEvent, ReactNode } from "react";
import { consultar } from "./api";
import type { Resultado as DatosResultado } from "./api";
import { Cargando } from "./Cargando";
import { Compositor } from "./Compositor";
import { Orbe } from "./Orbe";
import { preguntaValida } from "./pregunta";
import { Resultado } from "./Resultado";

type EstadoProcesamiento = "inactivo" | "procesando" | "completado" | "error";

interface ErrorVisible {
  mensaje: string;
  codigoReferencia?: string;
}

function Fondo() {
  return (
    <div className="fondo" aria-hidden="true">
      <span className="mancha mancha-turquesa" />
      <span className="mancha mancha-morado" />
      <span className="mancha mancha-naranja" />
      <span className="trama" />
      <span className="escaneo" />
    </div>
  );
}

function Cabecera({ onNueva, puedeReiniciar }: { onNueva: () => void; puedeReiniciar: boolean }) {
  return (
    <header className="cabecera">
      <div className="marca">
        <Orbe tamano="logo" />
        <h1>
          W <span className="marca-w">Connect</span>
        </h1>
        <span className="etiqueta-equipo">Asesores · Banco W</span>
      </div>
      {puedeReiniciar && (
        <button type="button" className="nueva" onClick={onNueva}>
          <Plus size={16} weight="bold" aria-hidden="true" />
          Nueva consulta
        </button>
      )}
    </header>
  );
}

function FilaAsistente({ children }: { children: ReactNode }) {
  return (
    <div className="fila-asistente entrada">
      <Orbe tamano="mini" />
      <div className="cuerpo-asistente">
        <span className="nombre-asistente">W Connect</span>
        {children}
      </div>
    </div>
  );
}

function Alerta({ error }: { error: ErrorVisible }) {
  return (
    <FilaAsistente>
      <div role="alert" className="alerta">
        <WarningCircle size={20} weight="duotone" className="icono-alerta" aria-hidden="true" />
        <div>
          <p>{error.mensaje}</p>
          {error.codigoReferencia !== undefined && (
            <p className="referencia">{`Código de referencia: ${error.codigoReferencia}`}</p>
          )}
        </div>
      </div>
    </FilaAsistente>
  );
}

function Bienvenida({ escuchando, onOrbe }: { escuchando: boolean; onOrbe: () => void }) {
  return (
    <div className="bienvenida">
      <button type="button" className="boton-orbe" onClick={onOrbe} aria-label="Escribir a W Connect">
        <Orbe tamano="grande" modo={escuchando ? "escuchando" : "reposo"} />
      </button>
      <div className="saludo entrada">
        <h2>Hola, soy W Connect.</h2>
        <p>
          Pregúntame por productos, políticas y procedimientos del banco. Te respondo solo con documentos
          oficiales y te muestro de dónde sale cada dato.
        </p>
      </div>
    </div>
  );
}

function useConsulta() {
  const [pregunta, setPregunta] = useState("");
  const [enviada, setEnviada] = useState<string | undefined>();
  const [estado, setEstado] = useState<EstadoProcesamiento>("inactivo");
  const [resultado, setResultado] = useState<DatosResultado | undefined>();
  const [error, setError] = useState<ErrorVisible | undefined>();

  async function enviar(evento: FormEvent) {
    evento.preventDefault();
    if (estado === "procesando" || !preguntaValida(pregunta)) return;
    setEstado("procesando");
    const texto = pregunta;
    setEnviada(texto);
    setPregunta("");
    setResultado(undefined);
    setError(undefined);
    const respuesta = await consultar(texto);
    if (respuesta.tipo === "ok") {
      setResultado(respuesta.resultado);
      setEstado("completado");
    } else {
      // FR-4: la pregunta vuelve a la caja para corregirla o reintentar, salvo que ya escribiera otra.
      setPregunta((actual) => (actual === "" ? texto : actual));
      setError(respuesta);
      setEstado("error");
    }
  }

  // Vuelve a la pantalla de inicio; con una consulta en curso no se ofrece.
  function reiniciar() {
    setPregunta("");
    setEnviada(undefined);
    setResultado(undefined);
    setError(undefined);
    setEstado("inactivo");
  }

  return { pregunta, setPregunta, enviada, estado, resultado, error, enviar, reiniciar };
}

interface PropsConversacion {
  enviada: string | undefined;
  procesando: boolean;
  error: ErrorVisible | undefined;
  resultado: DatosResultado | undefined;
  bienvenida: ReactNode;
}

function Conversacion({ enviada, procesando, error, resultado, bienvenida }: PropsConversacion) {
  const final = useRef<HTMLDivElement>(null);
  useEffect(() => {
    // Sin return: en Chrome scrollIntoView devuelve una Promise y React la tomaría como limpieza.
    final.current?.scrollIntoView?.({ block: "end", behavior: "smooth" });
  }, [procesando, error, resultado]);

  return (
    <main className="conversacion">
      {enviada === undefined && bienvenida}
      {enviada !== undefined && enviada.trim() !== "" && <p className="burbuja-usuario entrada">{enviada}</p>}
      <div role="status" aria-live="polite" className="estado-proceso">
        {procesando && <Cargando />}
      </div>
      {error && <Alerta error={error} />}
      {/* Siempre montada: los lectores de pantalla anuncian el resultado al insertarse en ella. */}
      <div aria-live="polite">
        {resultado && (
          <FilaAsistente>
            <Resultado resultado={resultado} />
          </FilaAsistente>
        )}
      </div>
      <div ref={final} />
    </main>
  );
}

export function App() {
  const { pregunta, setPregunta, enviada, estado, resultado, error, enviar, reiniciar } = useConsulta();
  const campo = useRef<HTMLInputElement>(null);
  const inicio = enviada === undefined;
  const procesando = estado === "procesando";
  return (
    <div className={inicio ? "app inicio" : "app conversando"}>
      <a className="saltar" href="#pregunta">
        Saltar a la pregunta
      </a>
      <Fondo />
      <Cabecera
        onNueva={() => {
          reiniciar();
          campo.current?.focus();
        }}
        puedeReiniciar={!inicio && !procesando}
      />
      <Conversacion
        enviada={enviada}
        procesando={procesando}
        error={error}
        resultado={resultado}
        bienvenida={<Bienvenida escuchando={pregunta.trim() !== ""} onOrbe={() => campo.current?.focus()} />}
      />
      <Compositor
        ref={campo}
        pregunta={pregunta}
        onCambio={setPregunta}
        onEnviar={enviar}
        procesando={procesando}
        conSugerencias={inicio}
      />
      <p className="pie">
        W Connect puede equivocarse: confirma siempre en la fuente citada. No escribas datos personales de
        clientes.
      </p>
    </div>
  );
}
