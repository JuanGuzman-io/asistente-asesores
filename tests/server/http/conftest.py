"""Fixtures compartidas de las pruebas de la API (T9, MDO-0001).

API asumida (design.md no fija cómo inyectar el redactor; sigue el estilo de `crear_app` de T3):

    crear_app(*, directorio_datos, excluidos, directorio_qdrant, ruta_sqlite, embeddings,
              redactor: Redactor | None = None) -> FastAPI

    `redactor=None` arma el real (`RedactorGemini(api_key=os.environ.get("GEMINI_API_KEY"))`); las
    pruebas inyectan siempre un doble. La clave nunca pasa por `crear_app` en estas pruebas.
    El `lifespan` crea el esquema `consultas` (`persistencia.esquema.crear_esquema`) y activa WAL.
    La ruta `POST /api/consultar` abre una conexión SQLite propia por petición y la cierra al terminar.

Sin red ni descarga de modelos: doble de embeddings, doble del redactor y `tmp_path`.
"""

import hashlib
import json
import re
import sqlite3
from collections.abc import Callable, Iterator, Sequence
from contextlib import AbstractContextManager, contextmanager
from dataclasses import dataclass
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from src.server.config import DIRECTORIO_DATOS, DOCUMENTOS_EXCLUIDOS
from src.server.dominio.modelos import Fragmento
from src.server.dominio.puertos import RespuestaRedactada
from src.server.http.app import crear_app

DIMENSION = 384


class EmbeddingsDoble:
    """Determinista: una base común (todo es 'cercano') más una bolsa de palabras (ordena)."""

    nombre = "doble-http"

    def __init__(self) -> None:
        self.textos: list[str] = []

    def embeber(self, textos: Sequence[str]) -> list[list[float]]:
        self.textos.extend(textos)
        return [self._vector(t) for t in textos]

    @staticmethod
    def _vector(texto: str) -> list[float]:
        base = [1 / DIMENSION**0.5] * DIMENSION
        bolsa = [0.0] * DIMENSION
        for palabra in re.findall(r"\w+", texto.lower()):
            bolsa[int.from_bytes(hashlib.sha256(palabra.encode()).digest()[:4]) % DIMENSION] += 1
        norma = sum(x * x for x in bolsa) ** 0.5 or 1.0
        return [b + 0.5 * x / norma for b, x in zip(base, bolsa, strict=True)]


class RedactorDoble:
    """Cita el fragmento 1; registra cada pregunta que recibe."""

    modo = "modelo"

    def __init__(self) -> None:
        self.llamadas: list[str] = []

    def redactar(self, pregunta: str, fragmentos: Sequence[Fragmento]) -> RespuestaRedactada:
        self.llamadas.append(pregunta)
        return RespuestaRedactada("Respuesta del doble.", [1])


@dataclass
class Entorno:
    ruta_sqlite: Path
    directorio_qdrant: Path
    embeddings: EmbeddingsDoble
    redactor: RedactorDoble

    def filas(self) -> list[sqlite3.Row]:
        con = sqlite3.connect(self.ruta_sqlite)
        con.row_factory = sqlite3.Row
        try:
            return con.execute("SELECT * FROM consultas ORDER BY id").fetchall()
        finally:
            con.close()


@pytest.fixture
def entorno(tmp_path: Path) -> Entorno:
    return Entorno(
        ruta_sqlite=tmp_path / "consultas.db",
        directorio_qdrant=tmp_path / "qdrant",
        embeddings=EmbeddingsDoble(),
        redactor=RedactorDoble(),
    )


@pytest.fixture
def arrancar(entorno: Entorno) -> Callable[..., AbstractContextManager[TestClient]]:
    @contextmanager
    def _arrancar(redactor: object | None = None) -> Iterator[TestClient]:
        app = crear_app(
            directorio_datos=DIRECTORIO_DATOS,
            excluidos=DOCUMENTOS_EXCLUIDOS,
            directorio_qdrant=entorno.directorio_qdrant,
            ruta_sqlite=entorno.ruta_sqlite,
            embeddings=entorno.embeddings,
            redactor=redactor or entorno.redactor,  # type: ignore[call-arg]
        )
        with TestClient(app, raise_server_exceptions=False) as cliente:
            entorno.embeddings.textos.clear()  # solo cuentan las llamadas posteriores al arranque
            yield cliente

    return _arrancar


@pytest.fixture
def cliente(arrancar: Callable[..., AbstractContextManager[TestClient]]) -> Iterator[TestClient]:
    with arrancar() as c:
        yield c


@pytest.fixture
def linea_json(caplog: pytest.LogCaptureFixture) -> Callable[[str], dict[str, object] | None]:
    """Busca la línea de log JSON de una petición (NFR-4) por su `requestId`; None si no hay."""

    def buscar(request_id: str) -> dict[str, object] | None:
        for registro in caplog.records:
            try:
                dato = json.loads(registro.getMessage())
            except ValueError:
                continue
            if isinstance(dato, dict) and dato.get("requestId") == request_id:
                return dato
        return None

    return buscar
