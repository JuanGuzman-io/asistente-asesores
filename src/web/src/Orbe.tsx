// Orbe de Bot-W (spec C-5): esfera con los colores de Banco W girando, anillos en órbita y pulsos.
// Es decorativo (aria-hidden); el modo cambia la velocidad y enciende los pulsos.
// La animación vive en clases CSS bajo prefers-reduced-motion: no-preference.

export type ModoOrbe = "reposo" | "escuchando" | "pensando";

interface Props {
  tamano: "grande" | "medio" | "mini" | "logo";
  modo?: ModoOrbe;
}

export function Orbe({ tamano, modo = "reposo" }: Props) {
  const completo = tamano === "grande" || tamano === "medio";
  return (
    <span className={`orbe orbe-${tamano}`} data-modo={modo} aria-hidden="true">
      {completo && (
        <>
          <span className="orbe-pulsos">
            <span />
            <span />
            <span />
          </span>
          <span className="orbe-anillo">
            <span className="orbe-satelite" />
          </span>
          <span className="orbe-anillo-interno">
            <span className="orbe-satelite" />
          </span>
          <span className="orbe-halo" />
        </>
      )}
      <span className="orbe-esfera">
        <span className="orbe-color" />
        <span className="orbe-brillo" />
      </span>
    </span>
  );
}
