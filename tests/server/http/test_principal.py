"""Punto de entrada `src.server.principal:app` (uvicorn, un solo worker por D13).

Importar el módulo no descarga el modelo ni indexa: eso pasa en el `lifespan`, que aquí no corre.
"""

import importlib

from fastapi import FastAPI

from src.server.config import DIRECTORIO_ALMACEN, DIRECTORIO_QDRANT, RUTA_SQLITE


def test_el_punto_de_entrada_expone_la_app_sin_arrancarla():
    principal = importlib.import_module("src.server.principal")

    assert isinstance(principal.app, FastAPI)
    assert DIRECTORIO_ALMACEN.is_dir()
    assert principal.app.router.lifespan_context is not None


def test_los_almacenes_viven_fuera_de_git_en_la_carpeta_almacen():
    assert DIRECTORIO_QDRANT.parent == DIRECTORIO_ALMACEN
    assert RUTA_SQLITE.parent == DIRECTORIO_ALMACEN
    gitignore = (DIRECTORIO_ALMACEN.parent / ".gitignore").read_text(encoding="utf-8")
    assert "almacen/" in gitignore.splitlines()
