from collections.abc import Sequence

from src.server.dominio.modelos import Fragmento, Fuente


def deduplicar_fuentes(fragmentos: Sequence[Fragmento]) -> list[Fuente]:
    fuentes: dict[tuple[str, str], Fuente] = {}
    for f in fragmentos:
        fuentes.setdefault((f.documento, f.seccion), Fuente(f.documento, f.seccion, f.texto))
    return list(fuentes.values())
