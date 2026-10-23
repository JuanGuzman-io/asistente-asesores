"""Fixtures compartidas de las pruebas de búsqueda (T3, T4): SQLite, Qdrant local y documentos."""

import sqlite3
from collections.abc import Iterator
from pathlib import Path

import pytest

from src.server.config import DOCUMENTOS_EXCLUIDOS
from src.server.dominio.modelos import Fragmento
from src.server.infraestructura.documentos.cargador import cargar_documentos

DATA = Path(__file__).resolve().parents[4] / "Data"


@pytest.fixture
def conexion(tmp_path: Path) -> Iterator[sqlite3.Connection]:
    con = sqlite3.connect(tmp_path / "indice.db")
    yield con
    con.close()


@pytest.fixture
def qdrant(tmp_path: Path):
    from qdrant_client import QdrantClient

    cliente = QdrantClient(path=str(tmp_path / "qdrant"))
    yield cliente
    cliente.close()


@pytest.fixture
def oficiales() -> list[Fragmento]:
    return cargar_documentos(DATA, DOCUMENTOS_EXCLUIDOS)
