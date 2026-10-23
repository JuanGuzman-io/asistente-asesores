"""T3 (MDO-0001) E2E: el arranque real de la app indexa la base documental (S-1.1, S-1.1/C1).

API asumida (design.md no define cómo inyectar; config.py solo tiene constantes de módulo, así que
la vía más simple es argumentos con nombre en la fábrica de la app):

    src/server/http/app.py
        crear_app(*, directorio_datos: Path, excluidos: Sequence[str], directorio_qdrant: Path,
                  ruta_sqlite: Path, embeddings: Embeddings) -> FastAPI
    El `lifespan` abre UN `QdrantClient(path=directorio_qdrant)` y una conexión SQLite, llama a
    `reconstruir_indice(...)` (ver tests/server/infraestructura/busqueda/test_indice.py) y cierra
    ambos al apagar. `Embeddings`: `nombre: str` y `embeber(textos) -> list[list[float]]`.

    Log de arranque (módulo `logging`, nivel INFO, cualquier logger): un mensaje que contiene
    `fragmentos=<n> embeddings_nuevos=<k> duracion_ms=<t>` con enteros o decimales; NFR-2 se mide ahí.
    Nunca incluye contenido de documentos excluidos.

Sin red ni descarga de modelos: doble de embeddings determinista y carpetas temporales.
"""

import hashlib
import logging
import re
import sqlite3
import unicodedata
from collections.abc import Sequence
from pathlib import Path

import pytest

from src.server.config import DIRECTORIO_DATOS, DOCUMENTOS_EXCLUIDOS
from src.server.http.app import crear_app

RESTRINGIDO = "Información restringida.md"
DIMENSION = 384
OFICIALES = {
    "Manual del Asesor Comercial",
    "Políticas de Atención",
    "Portafolio de Microseguros",
    "Procedimientos Operativos",
    "Productos de Crédito",
}
PATRON_LOG = re.compile(r"fragmentos=(\d+) embeddings_nuevos=(\d+) duracion_ms=(\d+(?:\.\d+)?)")


class EmbeddingsDoble:
    nombre = "doble-determinista"

    def __init__(self) -> None:
        self.textos: list[str] = []

    def embeber(self, textos: Sequence[str]) -> list[list[float]]:
        self.textos.extend(textos)
        return [
            [(b - 127.5) / 127.5 for b in hashlib.shake_256(t.encode()).digest(DIMENSION)]
            for t in textos
        ]


@pytest.fixture
def estado(tmp_path: Path) -> dict[str, Path]:
    return {"directorio_qdrant": tmp_path / "qdrant", "ruta_sqlite": tmp_path / "consultas.db"}


def _arrancar(estado: dict[str, Path], embeddings: EmbeddingsDoble):
    from fastapi.testclient import TestClient

    app = crear_app(
        directorio_datos=DIRECTORIO_DATOS,
        excluidos=DOCUMENTOS_EXCLUIDOS,
        embeddings=embeddings,
        **estado,
    )
    return TestClient(app)


def _lineas_arranque(caplog: pytest.LogCaptureFixture) -> list[re.Match[str]]:
    return [m for r in caplog.records if (m := PATRON_LOG.search(r.getMessage()))]


def test_s11_el_arranque_deja_indexados_los_cinco_oficiales(estado, caplog):
    caplog.set_level(logging.INFO)
    doble = EmbeddingsDoble()

    with _arrancar(estado, doble):
        pass

    con = sqlite3.connect(estado["ruta_sqlite"])
    try:
        filas = con.execute("SELECT documento, seccion, texto FROM fragmentos").fetchall()
        encontrados = con.execute(
            "SELECT count(*) FROM fragmentos_fts WHERE fragmentos_fts MATCH ?", ('"impuls"',)
        ).fetchone()[0]
    finally:
        con.close()
    assert {unicodedata.normalize("NFC", f[0]) for f in filas} == OFICIALES
    assert "Políticas de Atención" in {unicodedata.normalize("NFC", f[0]) for f in filas}
    assert all(documento and seccion and texto for documento, seccion, texto in filas)
    assert encontrados >= 1
    assert len(doble.textos) == len(filas)
    (linea,) = _lineas_arranque(caplog)
    assert int(linea.group(1)) == len(filas)
    assert int(linea.group(2)) == len(filas)


def test_s11_c1_el_arranque_no_indexa_nada_del_confidencial(estado, caplog):
    from qdrant_client import QdrantClient

    caplog.set_level(logging.INFO)
    restringido = (DIRECTORIO_DATOS / RESTRINGIDO).read_text(encoding="utf-8")
    assert "INT-8457" in restringido  # guarda: la prueba no es vacua
    doble = EmbeddingsDoble()

    with _arrancar(estado, doble):
        pass

    con = sqlite3.connect(estado["ruta_sqlite"])
    try:
        texto_sqlite = " ".join(
            " ".join(fila)
            for fila in con.execute("SELECT documento, seccion, texto FROM fragmentos")
        )
        en_fts = con.execute(
            "SELECT count(*) FROM fragmentos_fts WHERE fragmentos_fts MATCH ?",
            ('"INT-8457"',),
        ).fetchone()[0]
        total = con.execute("SELECT count(*) FROM fragmentos").fetchone()[0]
    finally:
        con.close()
    assert en_fts == 0
    assert "INT-8457" not in texto_sqlite
    # Qdrant: ni vectores de más ni términos del confidencial en el payload. Reabrir la carpeta
    # también prueba que el apagado liberó el bloqueo (D13).
    cliente = QdrantClient(path=str(estado["directorio_qdrant"]))
    try:
        puntos, _ = cliente.scroll("fragmentos", limit=1000, with_payload=True)
    finally:
        cliente.close()
    assert len(puntos) == total
    assert "INT-8457" not in repr([p.payload for p in puntos])
    assert [n for n, t in enumerate(doble.textos) if "INT-8457" in t] == []
    # El log nombra el excluido pero no revela su contenido.
    assert "INT-8457" not in caplog.text


def test_la_app_abre_un_solo_qdrant_client_y_lo_cierra_al_apagar(estado, monkeypatch):
    from qdrant_client import QdrantClient

    aperturas: list[object] = []
    cierres: list[object] = []
    inicial, cerrar = QdrantClient.__init__, QdrantClient.close

    def espia_init(self, *args, **kwargs):
        aperturas.append(self)
        inicial(self, *args, **kwargs)

    def espia_close(self, *args, **kwargs):
        cierres.append(self)
        return cerrar(self, *args, **kwargs)

    monkeypatch.setattr(QdrantClient, "__init__", espia_init)
    monkeypatch.setattr(QdrantClient, "close", espia_close)

    with _arrancar(estado, EmbeddingsDoble()):
        assert len(aperturas) == 1
        assert cierres == []  # sigue abierto mientras la app corre

    assert len(aperturas) == 1
    assert aperturas[0] in cierres  # se cerró al apagar
    monkeypatch.undo()
    # La carpeta ya no está bloqueada: un cliente nuevo la abre sin RuntimeError.
    QdrantClient(path=str(estado["directorio_qdrant"])).close()


def test_d13_si_falla_la_conexion_sqlite_el_cliente_qdrant_se_cierra(estado, monkeypatch):
    from qdrant_client import QdrantClient

    aperturas: list[object] = []
    cierres: list[object] = []
    inicial, cerrar = QdrantClient.__init__, QdrantClient.close

    def espia_init(self, *args, **kwargs):
        aperturas.append(self)
        inicial(self, *args, **kwargs)

    def espia_close(self, *args, **kwargs):
        cierres.append(self)
        return cerrar(self, *args, **kwargs)

    monkeypatch.setattr(QdrantClient, "__init__", espia_init)
    monkeypatch.setattr(QdrantClient, "close", espia_close)
    estado["ruta_sqlite"] = estado["ruta_sqlite"].parent / "no_existe" / "consultas.db"

    with pytest.raises(sqlite3.OperationalError):
        with _arrancar(estado, EmbeddingsDoble()):
            pass

    assert len(aperturas) == 1
    assert aperturas[0] in cierres  # el cliente se cerró pese al fallo de SQLite
    monkeypatch.undo()
    # La carpeta ya no está bloqueada: un cliente nuevo la abre sin RuntimeError.
    QdrantClient(path=str(estado["directorio_qdrant"])).close()


def test_nfr2_segundo_arranque_sin_cambios_no_calcula_embeddings_y_tarda_menos_de_2_s(
    estado, caplog
):
    caplog.set_level(logging.INFO)
    with _arrancar(estado, EmbeddingsDoble()):
        pass
    caplog.clear()
    segundo = EmbeddingsDoble()

    with _arrancar(estado, segundo):
        pass

    assert segundo.textos == []
    (linea,) = _lineas_arranque(caplog)
    assert int(linea.group(2)) == 0
    assert float(linea.group(3)) <= 2000
