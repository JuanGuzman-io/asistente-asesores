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
