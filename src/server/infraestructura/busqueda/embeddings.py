from collections.abc import Sequence
from typing import Any, Protocol

from src.server.config import MODELO_EMBEDDINGS

DIMENSION_EMBEDDINGS = 384


class Embeddings(Protocol):
    nombre: str

    def embeber(self, textos: Sequence[str]) -> list[list[float]]: ...


class EmbeddingsFastembed:
    """Adaptador real (ONNX local). El modelo se descarga en la primera llamada, no al importar."""

    def __init__(self, nombre: str = MODELO_EMBEDDINGS) -> None:
        self.nombre = nombre
        self._modelo: Any = None

    def embeber(self, textos: Sequence[str]) -> list[list[float]]:
        if self._modelo is None:
            from fastembed import TextEmbedding

            self._modelo = TextEmbedding(model_name=self.nombre)
        return [[float(x) for x in vector] for vector in self._modelo.embed(list(textos))]
