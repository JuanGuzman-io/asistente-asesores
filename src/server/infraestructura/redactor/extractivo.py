from collections.abc import Sequence

from src.server.dominio.modelos import Fragmento
from src.server.dominio.puertos import RespuestaRedactada

FRASE_INICIAL = "Esto es lo que encontré en la base documental:"
MAXIMO_FRAGMENTOS = 2


class RedactorExtractivo:
    """Respuesta sin modelo (D12): frase fija y hasta 2 fragmentos con `Documento > Sección`."""

    def redactar(self, pregunta: str, fragmentos: Sequence[Fragmento]) -> RespuestaRedactada:
        usados = fragmentos[:MAXIMO_FRAGMENTOS]
        bloques = [f"{f.documento} > {f.seccion}\n{f.texto}" for f in usados]
        respuesta = "\n\n".join([FRASE_INICIAL, *bloques])
        return RespuestaRedactada(
            respuesta=respuesta,
            fragmentos_usados=list(range(1, len(usados) + 1)),
        )
