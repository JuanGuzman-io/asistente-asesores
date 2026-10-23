// Caja para escribir la pregunta: grande y centrada al inicio, en píldora fija abajo durante la conversación.
// Al inicio ofrece preguntas sugeridas que solo llenan la caja, sin enviar (spec C-5).
import { ArrowUp } from "@phosphor-icons/react";
import { forwardRef } from "react";
import type { FormEvent } from "react";

export const SUGERENCIAS = [
  "Requisitos del Crédito Productivo Impulso",
  "¿Qué financia Agro Crece?",
  "Microseguros para clientes nuevos",
];

interface Props {
  pregunta: string;
  onCambio: (pregunta: string) => void;
  onEnviar: (evento: FormEvent) => void;
  procesando: boolean;
  conSugerencias: boolean;
}

function Sugerencias({ onElegir }: { onElegir: (texto: string) => void }) {
  return (
    <div className="sugerencias">
      {SUGERENCIAS.map((texto) => (
        <button key={texto} type="button" onClick={() => onElegir(texto)}>
          {texto}
        </button>
      ))}
    </div>
  );
}

export const Compositor = forwardRef<HTMLInputElement, Props>(function Compositor(
  { pregunta, onCambio, onEnviar, procesando, conSugerencias },
  campo,
) {
  function sugerir(texto: string) {
    onCambio(texto);
    if (campo && "current" in campo) campo.current?.focus();
  }

  return (
    <form onSubmit={onEnviar} className="compositor">
      <label htmlFor="pregunta" className="solo-lector">
        Pregunta
      </label>
      <div className="caja">
        <input
          ref={campo}
          id="pregunta"
          aria-describedby="pregunta-ayuda"
          autoComplete="off"
          autoFocus
          placeholder={conSugerencias ? "¿Qué necesitas saber hoy?" : "Haz otra pregunta…"}
          value={pregunta}
          onChange={(e) => onCambio(e.target.value)}
        />
        <div className="caja-pie">
          <p id="pregunta-ayuda" className="documentos">
            <span className="punto-en-linea" aria-hidden="true" />
            <span>Solo documentos oficiales</span>
            <span className="solo-lector">. Pulsa Enter para enviar.</span>
          </p>
          <button
            type="submit"
            className="enviar"
            disabled={procesando}
            aria-label="Consultar"
            title="Consultar"
          >
            <ArrowUp size={18} weight="bold" aria-hidden="true" />
          </button>
        </div>
      </div>
      {conSugerencias && <Sugerencias onElegir={sugerir} />}
    </form>
  );
});
