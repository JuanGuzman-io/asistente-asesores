from collections.abc import Sequence
from dataclasses import dataclass
from typing import Protocol

from src.server.dominio.modelos import Fragmento


@dataclass(frozen=True)
class ResultadoBusqueda:
    fragmentos: Sequence[Fragmento]
    hay_soporte: bool


class BuscadorDocumental(Protocol):
    def buscar(self, pregunta: str) -> ResultadoBusqueda: ...


@dataclass(frozen=True)
class RespuestaRedactada:
    respuesta: str
    # Posiciones 1-based en la lista numerada de fragmentos entregada al redactor (D7).
    fragmentos_usados: Sequence[int]
    partes_sin_soporte: Sequence[str] = ()


class Redactor(Protocol):
    def redactar(self, pregunta: str, fragmentos: Sequence[Fragmento]) -> RespuestaRedactada: ...
