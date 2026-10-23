"""Punto de entrada del backend.

`uv run uvicorn src.server.principal:app --port 8000 --workers 1` (un solo worker, D13: Qdrant local
bloquea su carpeta). Con `.env`: `uv run --env-file .env uvicorn ...`.
"""

from src.server.config import (
    DIRECTORIO_ALMACEN,
    DIRECTORIO_DATOS,
    DIRECTORIO_QDRANT,
    DOCUMENTOS_EXCLUIDOS,
    RUTA_SQLITE,
)
from src.server.http.app import crear_app
from src.server.infraestructura.busqueda.embeddings import EmbeddingsFastembed

DIRECTORIO_ALMACEN.mkdir(exist_ok=True)

app = crear_app(
    directorio_datos=DIRECTORIO_DATOS,
    excluidos=DOCUMENTOS_EXCLUIDOS,
    directorio_qdrant=DIRECTORIO_QDRANT,
    ruta_sqlite=RUTA_SQLITE,
    embeddings=EmbeddingsFastembed(),
)
