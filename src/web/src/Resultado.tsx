// Resultado de una consulta (D4): respuesta, estado y fuentes, siempre como texto de React.
import { CheckCircle, FileText, Question, ShieldWarning } from "@phosphor-icons/react";
import type { Icon } from "@phosphor-icons/react";
import type { Estado, Fuente, Resultado as DatosResultado } from "./api";

const PRE_WRAP = { whiteSpace: "pre-wrap" } as const;

const ICONO_ESTADO: Record<Estado, Icon> = {
  Exitosa: CheckCircle,
  "Sin información suficiente": Question,
  "Bloqueada por seguridad": ShieldWarning,
};

interface Props {
  resultado: DatosResultado;
}

function ListaFuentes({ fuentes }: { fuentes: Fuente[] }) {
  if (fuentes.length === 0) return <p className="sin-fuentes">Sin fuentes</p>;
  return (
    <ul className="fuentes">
      {fuentes.map((fuente, indice) => (
        <li key={indice}>
          <span className="ficha-fuente" aria-hidden="true">
            <FileText size={18} weight="duotone" />
          </span>
          <div>
            <strong>{`${fuente.documento} > ${fuente.seccion}`}</strong>
            <blockquote style={PRE_WRAP}>{fuente.fragmento}</blockquote>
          </div>
        </li>
      ))}
    </ul>
  );
}

export function Resultado({ resultado }: Props) {
  const IconoEstado = ICONO_ESTADO[resultado.estado];
  return (
    <section aria-label="Resultado de la consulta" className="resultado">
      <p className="linea-estado">
        <span>Estado: </span>
        <strong className="etiqueta-estado" data-estado={resultado.estado}>
          <IconoEstado size={14} weight="bold" aria-hidden="true" />
          {resultado.estado}
        </strong>
      </p>
      <h2>Respuesta</h2>
      <p className="respuesta" style={PRE_WRAP}>
        {resultado.respuesta}
      </p>
      <h2>Fuentes</h2>
      <ListaFuentes fuentes={resultado.fuentes} />
    </section>
  );
}
