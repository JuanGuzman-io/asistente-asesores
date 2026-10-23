// Resultado de una consulta (D4): respuesta, estado y fuentes, siempre como texto de React.
import type { Fuente, Resultado as DatosResultado } from "./api";

const PRE_WRAP = { whiteSpace: "pre-wrap" } as const;

interface Props {
  resultado: DatosResultado;
}

function ListaFuentes({ fuentes }: { fuentes: Fuente[] }) {
  if (fuentes.length === 0) return <p>Sin fuentes</p>;
  return (
    <ul>
      {fuentes.map((fuente, indice) => (
        <li key={indice}>
          <strong>{`${fuente.documento} > ${fuente.seccion}`}</strong>
          <blockquote style={PRE_WRAP}>{fuente.fragmento}</blockquote>
        </li>
      ))}
    </ul>
  );
}

export function Resultado({ resultado }: Props) {
  return (
    <section aria-label="Resultado de la consulta">
      <p>
        <span>Estado: </span>
        <strong>{resultado.estado}</strong>
      </p>
      <h2>Respuesta</h2>
      <p style={PRE_WRAP}>{resultado.respuesta}</p>
      <h2>Fuentes</h2>
      <ListaFuentes fuentes={resultado.fuentes} />
    </section>
  );
}
