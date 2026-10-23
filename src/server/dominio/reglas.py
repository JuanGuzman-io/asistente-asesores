from collections.abc import Sequence

from src.server.dominio.modelos import Fragmento, Fuente

MENSAJE_SIN_INFORMACION = "No tengo información suficiente para responder."
# D3: un solo texto para las tres categorías; no nombra la regla ni la categoría.
MENSAJE_BLOQUEO = (
    "No puedo responder esta consulta porque no cumple "
    "las políticas de seguridad de la información."
)


def deduplicar_fuentes(fragmentos: Sequence[Fragmento]) -> list[Fuente]:
    fuentes: dict[tuple[str, str], Fuente] = {}
    for f in fragmentos:
        fuentes.setdefault((f.documento, f.seccion), Fuente(f.documento, f.seccion, f.texto))
    return list(fuentes.values())
