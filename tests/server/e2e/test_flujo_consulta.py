"""T10 (MDO-0001) E2E: flujo crítico "Consulta respondida con fuentes y registrada".

Punta a punta por HTTP: `crear_app` real sobre `Data/` (cargador, índice SQLite + Qdrant local,
buscador híbrido, umbrales de `config.py`, redactor extractivo, registro en `consultas`). Solo el
embedding es un doble, para que la prueba sea rápida y no use red (standards.md: las pruebas no
descargan modelos). El doble NO calibra umbrales: eso lo hacen las evals con el modelo real.

Traza: S-4.1 y S-4.1/C1 (AC-3, AC-6, AC-14), "token interno" / "clave temporal" (Done when,
AC-11), S-10.1 (AC-11), S-11.1 (AC-14, rechazadas 413/415/422 sin registro) y S-5.2 (AC-5 sin
modelo, `RedactorExtractivo`).

Doble de embeddings ("oráculo léxico"): cada fragmento indexado es un vector unitario propio y la
pregunta es la suma de los fragmentos que comparten palabras significativas (sección + texto) más
una componente ortogonal; el coseno con un fragmento es `w_i / sqrt(sum(w^2) + 1)`: alto si la
pregunta comparte varias palabras con ese fragmento y 0 si no comparte ninguna.
"""

import json
import re
import sqlite3
import unicodedata
from collections.abc import Iterator, Sequence
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from src.server.config import DIRECTORIO_DATOS, DOCUMENTOS_EXCLUIDOS
from src.server.dominio.reglas import MENSAJE_SIN_INFORMACION
from src.server.http.app import crear_app
from src.server.infraestructura.busqueda.indice import texto_indexable
from src.server.infraestructura.documentos.cargador import cargar_documentos
from src.server.infraestructura.redactor.extractivo import RedactorExtractivo

RUTA = "/api/consultar"
PREGUNTA_PDF = "¿Cuál es el monto máximo del Crédito Productivo Impulso?"
PREGUNTA_PARCIAL = (
    "¿Cuál es el monto máximo del Crédito Productivo Impulso y cuál es su tasa de interés?"
)
ENCABEZADO_EXTRACTIVO = "Esto es lo que encontré en la base documental:"
RESTRINGIDO = "Información restringida.md"
DIMENSION = 384


def _palabras(texto: str) -> set[str]:
    sin_tildes = unicodedata.normalize("NFD", texto.lower()).encode("ascii", "ignore").decode()
    return {p for p in re.findall(r"[a-z0-9]+", sin_tildes) if len(p) > 3}


class EmbeddingsOraculo:
    nombre = "oraculo-lexico"

    def __init__(self) -> None:
        fragmentos = cargar_documentos(DIRECTORIO_DATOS, DOCUMENTOS_EXCLUIDOS)
        # Texto que embebe el índice: el mismo `texto_indexable` que usa `indice.py`.
        self._indice = {texto_indexable(f): n for n, f in enumerate(fragmentos)}
        self._palabras = [_palabras(f"{f.seccion} {f.texto}") for f in fragmentos]

    def embeber(self, textos: Sequence[str]) -> list[list[float]]:
        return [self._vector(t) for t in textos]

    def _vector(self, texto: str) -> list[float]:
        vector = [0.0] * DIMENSION
        if texto in self._indice:  # un fragmento de la base: vector unitario propio
            vector[self._indice[texto]] = 1.0
            return vector
        pregunta = _palabras(texto)
        for n, palabras in enumerate(self._palabras):
            vector[n] = float(len(pregunta & palabras))
        vector[DIMENSION - 1] = 1.0
        norma = sum(x * x for x in vector) ** 0.5
        return [x / norma for x in vector]


class Entorno:
    def __init__(self, tmp_path: Path) -> None:
        self.ruta_sqlite = tmp_path / "consultas.db"
        self.directorio_qdrant = tmp_path / "qdrant"

    def filas(self) -> list[sqlite3.Row]:
        con = sqlite3.connect(self.ruta_sqlite)
        con.row_factory = sqlite3.Row
        try:
            return con.execute("SELECT * FROM consultas ORDER BY id").fetchall()
        finally:
            con.close()


@pytest.fixture
def entorno(tmp_path: Path) -> Entorno:
    return Entorno(tmp_path)


@pytest.fixture
def cliente(entorno: Entorno) -> Iterator[TestClient]:
    app = crear_app(
        directorio_datos=DIRECTORIO_DATOS,
        excluidos=DOCUMENTOS_EXCLUIDOS,
        directorio_qdrant=entorno.directorio_qdrant,
        ruta_sqlite=entorno.ruta_sqlite,
        embeddings=EmbeddingsOraculo(),
        redactor=RedactorExtractivo(),
    )
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c


def _lineas_restringidas() -> list[str]:
    """Líneas significativas del confidencial, leídas en la prueba: nunca copiadas al código."""
    texto = (DIRECTORIO_DATOS / RESTRINGIDO).read_text(encoding="utf-8")
    lineas = [li.strip() for li in texto.splitlines()]
    return [li for li in lineas if len(li) >= 8 and not li.startswith("#")]


def _afirmar_sin_informacion(respuesta) -> dict:
    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert (
        cuerpo["respuesta"]
        == MENSAJE_SIN_INFORMACION
        == "No tengo información suficiente para responder."
    )
    assert cuerpo["fuentes"] == []
    assert cuerpo["estado"] == "Sin información suficiente"
    return cuerpo


# --- S-4.1 y S-4.1/C1 ---------------------------------------------------------------------------


def test_s4_1_la_pregunta_del_pdf_responde_200_con_el_monto_su_fuente_y_queda_registrada(
    cliente, entorno
):
    respuesta = cliente.post(RUTA, json={"pregunta": PREGUNTA_PDF})

    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert set(cuerpo) == {"respuesta", "fuentes", "estado"}
    assert cuerpo["estado"] == "Exitosa"
    assert "$50.000.000" in cuerpo["respuesta"]
    # S-4.1/C1 y AC-6: al menos una fuente, completa, y la del Crédito Productivo Impulso.
    assert len(cuerpo["fuentes"]) >= 1
    assert all(f["documento"] and f["seccion"] and f["fragmento"] for f in cuerpo["fuentes"])
    primera = cuerpo["fuentes"][0]
    assert (primera["documento"], primera["seccion"]) == (
        "Productos de Crédito",
        "Crédito Productivo Impulso",
    )
    assert "$50.000.000" in primera["fragmento"]
    # AC-14: una fila con los cinco campos; las fuentes registradas son las devueltas.
    (fila,) = entorno.filas()
    assert fila["pregunta"] == PREGUNTA_PDF
    assert fila["respuesta"] == cuerpo["respuesta"]
    assert fila["estado"] == "EXITOSA"
    assert fila["fecha_hora"]
    assert json.loads(fila["fuentes"]) == cuerpo["fuentes"]
    assert fila["request_id"] == respuesta.headers["X-Request-Id"]


# --- Done when: token interno y clave temporal (AC-11, confidencial) ---------------------------


@pytest.mark.parametrize("pregunta", ["¿Cuál es el token interno?", "¿Cuál es la clave temporal?"])
def test_el_confidencial_no_se_devuelve_ni_se_registra(cliente, entorno, pregunta):
    lineas = _lineas_restringidas()
    assert lineas  # guarda: la prueba no es vacua

    respuesta = cliente.post(RUTA, json={"pregunta": pregunta})

    cuerpo = _afirmar_sin_informacion(respuesta)
    serializado = respuesta.text
    assert not [li for li in lineas if li in serializado]
    assert RESTRINGIDO.removesuffix(".md") not in serializado
    (fila,) = entorno.filas()
    assert fila["estado"] == "SIN_INFORMACION"
    assert not [li for li in lineas if li in fila["respuesta"] or li in fila["fuentes"]]
    assert cuerpo["estado"] == "Sin información suficiente"


# --- S-10.1 -------------------------------------------------------------------------------------


def test_s10_1_una_pregunta_sin_soporte_responde_el_mensaje_fijo_y_queda_registrada(
    cliente, entorno
):
    pregunta = "¿Cuál es el horario de atención de las agencias?"

    respuesta = cliente.post(RUTA, json={"pregunta": pregunta})

    _afirmar_sin_informacion(respuesta)
    (fila,) = entorno.filas()
    assert fila["pregunta"] == pregunta
    assert fila["respuesta"] == MENSAJE_SIN_INFORMACION
    assert fila["fuentes"] == "[]"
    assert fila["estado"] == "SIN_INFORMACION"
    assert fila["modo"] == "ninguno"  # sin soporte no se redacta (D4)


def test_s10_3_fuera_de_tema_no_es_bloqueada_por_seguridad(cliente):
    respuesta = cliente.post(RUTA, json={"pregunta": "¿Va a llover mañana en Bogotá?"})

    cuerpo = _afirmar_sin_informacion(respuesta)
    assert cuerpo["estado"] != "Bloqueada por seguridad"


# --- S-11.1 -------------------------------------------------------------------------------------


def test_s11_1_cada_consulta_procesada_tiene_su_registro_y_las_rechazadas_ninguno(cliente, entorno):
    exitosa = cliente.post(RUTA, json={"pregunta": PREGUNTA_PDF})
    sin_info = cliente.post(
        RUTA, json={"pregunta": "¿Cuál es el horario de atención de las agencias?"}
    )
    assert (exitosa.status_code, sin_info.status_code) == (200, 200)
    assert len(entorno.filas()) == 2

    rechazadas = [
        cliente.post(RUTA, content=b"{}", headers={"Content-Type": "text/plain"}),  # 415
        cliente.post(
            RUTA,
            content=b'{"pregunta": "' + b"a" * 17_000 + b'"}',
            headers={"Content-Type": "application/json"},
        ),  # 413
        cliente.post(RUTA, json={"pregunta": ""}),  # 422
        cliente.post(RUTA, json={"pregunta": "a" * 1001}),  # 422
    ]

    assert [r.status_code for r in rechazadas] == [415, 413, 422, 422]
    filas = entorno.filas()
    assert len(filas) == 2  # ninguna rechazada dejó registro
    por_estado = {f["estado"]: f for f in filas}
    assert set(por_estado) == {"EXITOSA", "SIN_INFORMACION"}
    campos = ("pregunta", "fecha_hora", "respuesta", "fuentes", "estado")
    for fila in filas:
        assert all(fila[c] not in (None, "") for c in campos)
    assert json.loads(por_estado["EXITOSA"]["fuentes"]) == exitosa.json()["fuentes"]
    assert json.loads(por_estado["SIN_INFORMACION"]["fuentes"]) == sin_info.json()["fuentes"] == []


# --- S-5.2 --------------------------------------------------------------------------------------


def test_s5_2_sin_modelo_la_pregunta_de_monto_y_tasa_trae_el_fragmento_con_su_fuente(
    cliente, entorno
):
    respuesta = cliente.post(RUTA, json={"pregunta": PREGUNTA_PARCIAL})

    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert cuerpo["estado"] == "Exitosa"
    assert cuerpo["respuesta"].startswith(ENCABEZADO_EXTRACTIVO)
    assert "$50.000.000" in cuerpo["respuesta"]
    fuentes = [(f["documento"], f["seccion"]) for f in cuerpo["fuentes"]]
    assert ("Productos de Crédito", "Crédito Productivo Impulso") in fuentes
    assert all(f["fragmento"] for f in cuerpo["fuentes"])
    # BUT it must NOT: dar una tasa ni afirmar que cubre toda la pregunta.
    assert "%" not in cuerpo["respuesta"]
    assert not re.search(r"tasa[^.\n]{0,30}\d", cuerpo["respuesta"].lower())
    assert "No encontré información sobre" not in cuerpo["respuesta"]
    (fila,) = entorno.filas()
    assert fila["modo"] == "extractivo"
    assert fila["estado"] == "EXITOSA"
