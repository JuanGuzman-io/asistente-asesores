"""T11 (MDO-0001) E2E: el flujo de punta a punta sigue extractivo si Gemini cae (AC-16).

Traza: S-12.1 (cliente caído: 200, `Exitosa`, fragmentos, fuentes y fila con `modo` `extractivo`) y
S-12.2 (`crear_app(redactor=None)` sin `GEMINI_API_KEY`: no se crea el cliente y la respuesta es
extractiva). `crear_app` real sobre `Data/`; solo el embedding (oráculo léxico de T10) y el cliente
de Gemini son dobles: sin red.
"""

import json
import sqlite3
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest
from fastapi.testclient import TestClient
from test_flujo_consulta import EmbeddingsOraculo

from src.server.config import DIRECTORIO_DATOS, DOCUMENTOS_EXCLUIDOS
from src.server.http.app import crear_app
from src.server.infraestructura.redactor.gemini import RedactorGemini

RUTA = "/api/consultar"
PREGUNTA = "¿Cuál es el monto máximo del Crédito Productivo Impulso?"
ENCABEZADO = "Esto es lo que encontré en la base documental:"


class ClienteCaido:
    def __init__(self, error: Exception) -> None:
        self.llamadas = 0
        self.models = self
        self._error = error

    def generate_content(self, **_: object) -> object:
        self.llamadas += 1
        raise self._error


class ClienteSecuencial:
    """Cada llamada devuelve un texto JSON o lanza una excepción, en orden."""

    def __init__(self, *resultados: str | Exception) -> None:
        self.llamadas = 0
        self.models = self
        self._resultados = list(resultados)

    def generate_content(self, **_: object) -> object:
        self.llamadas += 1
        resultado = self._resultados.pop(0)
        if isinstance(resultado, Exception):
            raise resultado
        return SimpleNamespace(text=resultado)


SALIDA_VALIDA = json.dumps(
    {"respuesta": "El monto máximo es de $50.000.000.", "fragmentos_usados": [1]}
)


def _filas(ruta: Path) -> list[sqlite3.Row]:
    con = sqlite3.connect(ruta)
    con.row_factory = sqlite3.Row
    try:
        return con.execute("SELECT * FROM consultas ORDER BY id").fetchall()
    finally:
        con.close()


def _app(tmp_path: Path, redactor: Any) -> TestClient:
    app = crear_app(
        directorio_datos=DIRECTORIO_DATOS,
        excluidos=DOCUMENTOS_EXCLUIDOS,
        directorio_qdrant=tmp_path / "qdrant",
        ruta_sqlite=tmp_path / "consultas.db",
        embeddings=EmbeddingsOraculo(),
        redactor=redactor,
    )
    return TestClient(app, raise_server_exceptions=False)


def _afirmar_extractiva_registrada(respuesta: Any, ruta_sqlite: Path) -> None:
    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert cuerpo["estado"] == "Exitosa"
    assert cuerpo["respuesta"].startswith(ENCABEZADO)
    assert "$50.000.000" in cuerpo["respuesta"]
    assert len(cuerpo["fuentes"]) >= 1
    assert all(f["documento"] and f["seccion"] and f["fragmento"] for f in cuerpo["fuentes"])
    assert (cuerpo["fuentes"][0]["documento"], cuerpo["fuentes"][0]["seccion"]) == (
        "Productos de Crédito",
        "Crédito Productivo Impulso",
    )
    (fila,) = _filas(ruta_sqlite)
    assert fila["modo"] == "extractivo"
    assert fila["estado"] == "EXITOSA"
    assert fila["respuesta"] == cuerpo["respuesta"]
    assert fila["request_id"] == respuesta.headers["X-Request-Id"]


@pytest.mark.parametrize(
    "error",
    [RuntimeError("503 del servicio"), TimeoutError("timeout de 5 s")],
    ids=["error", "tiempo-agotado"],
)
def test_s12_1_con_gemini_caido_responde_200_extractiva_con_fuentes_y_registra_extractivo(
    tmp_path, error
):
    cliente_gemini = ClienteCaido(error)
    redactor = RedactorGemini(api_key="clave-falsa", fabrica_cliente=lambda _: cliente_gemini)

    with _app(tmp_path, redactor) as http:
        respuesta = http.post(RUTA, json={"pregunta": PREGUNTA})

    _afirmar_extractiva_registrada(respuesta, tmp_path / "consultas.db")
    assert cliente_gemini.llamadas == 1  # sin reintentos


def test_s12_1_dos_consultas_con_gemini_caido_registran_extractivo_las_dos_veces(tmp_path):
    redactor = RedactorGemini(
        api_key="clave-falsa", fabrica_cliente=lambda _: ClienteCaido(RuntimeError("caído"))
    )

    with _app(tmp_path, redactor) as http:
        r1 = http.post(RUTA, json={"pregunta": PREGUNTA})
        r2 = http.post(RUTA, json={"pregunta": PREGUNTA})

    assert r1.status_code == r2.status_code == 200
    assert [f["modo"] for f in _filas(tmp_path / "consultas.db")] == ["extractivo", "extractivo"]


def test_s12_2_crear_app_sin_gemini_api_key_no_crea_el_cliente_y_responde_extractiva(
    tmp_path, monkeypatch
):
    from google import genai

    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    creados: list[object] = []
    monkeypatch.setattr(genai, "Client", lambda *a, **k: creados.append((a, k)))

    with _app(tmp_path, None) as http:
        respuesta = http.post(RUTA, json={"pregunta": PREGUNTA})

    assert creados == []
    _afirmar_extractiva_registrada(respuesta, tmp_path / "consultas.db")


def test_s12_1_modelo_y_luego_gemini_caido_registra_modelo_y_luego_extractivo(tmp_path):
    """Mismo redactor compartido: éxito del modelo y después caída; el `modo` no debe quedar rancio."""
    cliente = ClienteSecuencial(SALIDA_VALIDA, RuntimeError("caído"))
    redactor = RedactorGemini(api_key="clave-falsa", fabrica_cliente=lambda _: cliente)

    with _app(tmp_path, redactor) as http:
        r1 = http.post(RUTA, json={"pregunta": PREGUNTA})
        r2 = http.post(RUTA, json={"pregunta": PREGUNTA})

    assert r1.status_code == r2.status_code == 200
    assert r1.json()["respuesta"] == "El monto máximo es de $50.000.000."
    assert r2.json()["respuesta"].startswith(ENCABEZADO)
    assert [f["modo"] for f in _filas(tmp_path / "consultas.db")] == ["modelo", "extractivo"]
    assert cliente.llamadas == 2
