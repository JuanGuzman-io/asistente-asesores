"""T9 (MDO-0001) Límites del cuerpo y tipo de contenido (D8): 413 y 415 en RFC 9457.

Traza: S-9.1 (413 con y sin `Content-Length`), S-9.2 (415 con `text/plain` o sin tipo), AC-10,
S-11.1/C1 y AC-14/C1 (413, 415 y 422 no dejan filas en `consultas` ni consultan documentos).

API asumida y fixtures: ver `conftest.py` y `test_consultar_api.py`. El límite es de 16.384 bytes
de cuerpo; el middleware rechaza antes de validar (un cuerpo de 16.385 bytes responde 413, no 422).
"""

import uuid

import pytest

RUTA = "/api/consultar"
PREGUNTA_VALIDA = "¿Cuál es el monto máximo del Crédito Productivo Impulso?"
LIMITE = 16 * 1024
CAMPOS_PROBLEMA = {"type", "title", "status", "detail", "requestId"}
CUERPO_VALIDO = b'{"pregunta": "monto maximo del credito impulso"}'
JSON = {"Content-Type": "application/json"}


def _cuerpo_json(total_bytes: int) -> bytes:
    """JSON válido de `pregunta` con exactamente `total_bytes` bytes (ASCII)."""
    relleno = total_bytes - len(b'{"pregunta": ""}')
    cuerpo = b'{"pregunta": "' + b"a" * relleno + b'"}'
    assert len(cuerpo) == total_bytes
    return cuerpo


def _afirmar_problema(respuesta, codigo: int) -> None:
    assert respuesta.status_code == codigo
    assert respuesta.headers["content-type"].startswith("application/problem+json")
    cuerpo = respuesta.json()
    assert CAMPOS_PROBLEMA <= set(cuerpo)
    assert cuerpo["status"] == codigo
    assert isinstance(cuerpo["detail"], str) and cuerpo["detail"].strip()
    assert cuerpo["requestId"] == respuesta.headers["X-Request-Id"]
    assert uuid.UUID(cuerpo["requestId"]).version == 4


def _sin_efectos(entorno) -> None:
    assert entorno.embeddings.textos == []
    assert entorno.redactor.llamadas == []
    assert entorno.filas() == []


def _trozos(cuerpo: bytes, tamano: int = 4096):
    for i in range(0, len(cuerpo), tamano):
        yield cuerpo[i : i + tamano]


# --- S-9.1: 413 --------------------------------------------------------------------------------


def test_s9_1_cuerpo_de_16385_bytes_con_content_length_responde_413_problema(cliente, entorno):
    respuesta = cliente.post(RUTA, content=_cuerpo_json(LIMITE + 1), headers=JSON)

    assert respuesta.request.headers["Content-Length"] == str(LIMITE + 1)
    _afirmar_problema(respuesta, 413)
    _sin_efectos(entorno)


def test_s9_1_cuerpo_de_16385_bytes_sin_content_length_responde_413_problema(cliente, entorno):
    respuesta = cliente.post(RUTA, content=_trozos(_cuerpo_json(LIMITE + 1)), headers=JSON)

    assert "content-length" not in respuesta.request.headers  # llega por Transfer-Encoding: chunked
    _afirmar_problema(respuesta, 413)
    _sin_efectos(entorno)


def test_s9_1_cuerpo_muy_superior_al_limite_sin_content_length_responde_413(cliente, entorno):
    respuesta = cliente.post(RUTA, content=_trozos(_cuerpo_json(10 * LIMITE)), headers=JSON)

    _afirmar_problema(respuesta, 413)
    _sin_efectos(entorno)


def test_s9_1_cuerpo_de_exactamente_16384_bytes_no_se_rechaza_con_413(cliente, entorno):
    # En el límite pasa el middleware; la validación lo rechaza por largo (422), no por tamaño.
    respuesta = cliente.post(RUTA, content=_cuerpo_json(LIMITE), headers=JSON)

    _afirmar_problema(respuesta, 422)
    _sin_efectos(entorno)


# --- S-9.2: 415 --------------------------------------------------------------------------------


@pytest.mark.parametrize(
    "tipo",
    ["text/plain", "application/x-www-form-urlencoded", "multipart/form-data", "application/xml"],
)
def test_s9_2_content_type_distinto_de_json_responde_415_problema(cliente, entorno, tipo):
    respuesta = cliente.post(RUTA, content=CUERPO_VALIDO, headers={"Content-Type": tipo})

    _afirmar_problema(respuesta, 415)
    _sin_efectos(entorno)


def test_s9_2_sin_content_type_responde_415_problema(cliente, entorno):
    respuesta = cliente.post(RUTA, content=CUERPO_VALIDO)

    assert "content-type" not in respuesta.request.headers
    _afirmar_problema(respuesta, 415)
    _sin_efectos(entorno)


@pytest.mark.parametrize(
    "tipo", ["application/json", "application/json; charset=utf-8", "Application/JSON"]
)
def test_s9_2_application_json_con_o_sin_charset_si_se_procesa(cliente, entorno, tipo):
    respuesta = cliente.post(RUTA, content=CUERPO_VALIDO, headers={"Content-Type": tipo})

    assert respuesta.status_code == 200
    assert len(entorno.filas()) == 1


# --- S-11.1/C1 y AC-14/C1 ----------------------------------------------------------------------


def test_s11_1_c1_tras_413_415_y_422_la_tabla_consultas_no_tiene_filas_nuevas(cliente, entorno):
    assert cliente.post(RUTA, json={"pregunta": PREGUNTA_VALIDA}).status_code == 200
    assert len(entorno.filas()) == 1  # control: una válida sí registra

    r413 = cliente.post(RUTA, content=_cuerpo_json(LIMITE + 1), headers=JSON)
    r415 = cliente.post(RUTA, content=CUERPO_VALIDO, headers={"Content-Type": "text/plain"})
    r422 = cliente.post(RUTA, json={"pregunta": "   "})

    assert (r413.status_code, r415.status_code, r422.status_code) == (413, 415, 422)
    assert len(entorno.filas()) == 1
    assert entorno.redactor.llamadas == [PREGUNTA_VALIDA]  # solo la válida llegó al redactor
