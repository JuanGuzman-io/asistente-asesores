// Indicador de procesamiento: orbe pensando, texto de estado con puntos y líneas de carga.
// Solo el texto se anuncia; el resto es decorativo. La animación vive en clases CSS.
import { Orbe } from "./Orbe";

export const TEXTO_PROCESANDO = "Procesando consulta…";

export function Cargando() {
  return (
    <div className="cargando">
      <Orbe tamano="medio" modo="pensando" />
      <p className="texto-cargando">
        <span>{TEXTO_PROCESANDO}</span>
        <span className="puntos" aria-hidden="true">
          <span />
          <span />
          <span />
        </span>
      </p>
      <div className="lineas-carga" aria-hidden="true">
        <span />
        <span />
        <span />
        <span />
      </div>
    </div>
  );
}
