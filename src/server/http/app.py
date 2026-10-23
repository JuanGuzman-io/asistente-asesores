import os
import sqlite3
import threading
from collections.abc import AsyncIterator, Sequence
from contextlib import asynccontextmanager, closing
from pathlib import Path

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from qdrant_client import QdrantClient
from starlette.exceptions import HTTPException as StarletteHTTPException

from src.server.dominio.puertos import Redactor
from src.server.http.logs import configurar_logs
from src.server.http.middleware import MiddlewareSolicitud
from src.server.http.problemas import manejar_http, manejar_validacion
from src.server.http.rutas import router
from src.server.infraestructura.busqueda.embeddings import Embeddings
from src.server.infraestructura.busqueda.indice import reconstruir_indice
from src.server.infraestructura.documentos.cargador import cargar_documentos
from src.server.infraestructura.persistencia.esquema import crear_esquema
from src.server.infraestructura.redactor.gemini import RedactorGemini


def crear_app(
    *,
    directorio_datos: Path,
    excluidos: Sequence[str],
    directorio_qdrant: Path,
    ruta_sqlite: Path,
    embeddings: Embeddings,
    redactor: Redactor | None = None,
) -> FastAPI:
    configurar_logs()

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        qdrant = QdrantClient(path=str(directorio_qdrant))
        try:
            # Esta conexión solo sirve al arranque; cada petición abre la suya (tabla ACID).
            with closing(sqlite3.connect(ruta_sqlite)) as conexion:
                conexion.execute("PRAGMA journal_mode=WAL")
                crear_esquema(conexion)
                fragmentos = cargar_documentos(directorio_datos, excluidos)
                reconstruir_indice(
                    fragmentos, conexion=conexion, qdrant=qdrant, embeddings=embeddings
                )
            app.state.qdrant = qdrant
            app.state.ruta_sqlite = ruta_sqlite
            app.state.embeddings = embeddings
            # La clave se lee solo de `os.environ` (`uv run --env-file .env ...`).
            app.state.redactor = redactor or RedactorGemini(
                api_key=os.environ.get("GEMINI_API_KEY")
            )
            app.state.candado_redactor = threading.Lock()
            yield
        finally:
            qdrant.close()
            # Suelta la referencia en este hilo: `QdrantClient.__del__` vuelve a cerrar y falla
            # (sqlite3) si el recolector corre en otro hilo.
            app.state.qdrant = None

    app = FastAPI(lifespan=lifespan)
    app.add_middleware(MiddlewareSolicitud)
    app.add_exception_handler(RequestValidationError, manejar_validacion)
    app.add_exception_handler(StarletteHTTPException, manejar_http)
    app.include_router(router)
    return app
