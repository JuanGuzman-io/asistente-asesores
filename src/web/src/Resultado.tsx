// Resultado de una consulta (D4 enmendado): respuesta, estado y fuentes; el Markdown del servicio
// se pinta con formato mediante TextoMarkdown, sin HTML ni enlaces (AC-1/C3).
import { CheckCircle, FileText, Question, ShieldWarning } from "@phosphor-icons/react";
import type { Icon } from "@phosphor-icons/react";
import type { Estado, Fuente, Resultado as DatosResultado } from "./api";
import { TextoMarkdown } from "./TextoMarkdown";

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
            <blockquote className="md">
              <TextoMarkdown texto={fuente.fragmento} />
            </blockquote>
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
      <div className="respuesta md">
        <TextoMarkdown texto={resultado.respuesta} />
      </div>
      <h2>Fuentes</h2>
      <ListaFuentes fuentes={resultado.fuentes} />
    </section>
  );
}
