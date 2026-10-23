import sqlite3
from collections.abc import AsyncIterator, Sequence
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from qdrant_client import QdrantClient

from src.server.infraestructura.busqueda.embeddings import Embeddings
from src.server.infraestructura.busqueda.indice import reconstruir_indice
from src.server.infraestructura.documentos.cargador import cargar_documentos


def crear_app(
    *,
    directorio_datos: Path,
    excluidos: Sequence[str],
    directorio_qdrant: Path,
    ruta_sqlite: Path,
    embeddings: Embeddings,
) -> FastAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        qdrant = QdrantClient(path=str(directorio_qdrant))
        conexion: sqlite3.Connection | None = None
        try:
            conexion = sqlite3.connect(ruta_sqlite, check_same_thread=False)
            fragmentos = cargar_documentos(directorio_datos, excluidos)
            reconstruir_indice(fragmentos, conexion=conexion, qdrant=qdrant, embeddings=embeddings)
            app.state.qdrant = qdrant
            app.state.conexion = conexion
            yield
        finally:
            if conexion is not None:
                conexion.close()
            qdrant.close()

    return FastAPI(lifespan=lifespan)
