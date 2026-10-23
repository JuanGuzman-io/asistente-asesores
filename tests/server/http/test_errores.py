"""T12 (MDO-0001) Una falla inesperada responde 500 sin exponer detalles internos.

Traza: S-13.1 y AC-15 (500 `application/problem+json` con `requestId` y `detail` genérico cuando la
búsqueda lanza), S-13.1/C1 y AC-15/C1 (el cuerpo no lleva trazas, rutas, archivos internos, SQL ni la
pregunta), S-11.2 (si falla el insert de `consultas` responde el mismo 500) y NFR-4 (el log lleva
`requestId` y el tipo del error, nunca la pregunta ni el mensaje de la excepción).

Complementa los 500 de T9 (`test_consultar_api.py`, redactor que falla y tabla borrada): aquí falla la
búsqueda, se fija el contrato completo del cuerpo y se exige una línea de log con el tipo del error.
Los fallos se hacen con dobles inyectados; la pregunta y el mensaje de la excepción llevan marcas
únicas para detectar cualquier fuga.
"""

import logging
import sqlite3

import pytest

RUTA = "/api/consultar"
MARCA_PREGUNTA = "cliente-Zeta-4821"  # pragma: allowlist secret
MARCA_MENSAJE = "mensaje-interno-9137"
PREGUNTA = f"{MARCA_PREGUNTA} monto maximo del credito impulso"
DETALLE_GENERICO = "Ocurrió un error interno. Inténtalo de nuevo."
PROHIBIDOS_EN_CUERPO = (
    "Traceback",
    'File "',
    "/Users/",
    "/home/",
    "src/",
    ".py",
    "SELECT",
    "INSERT",
    "sqlite",
    "consultas",
    MARCA_PREGUNTA,
    MARCA_MENSAJE,
)


class ErrorDeBusqueda(Exception):
    pass


def _falla_busqueda(entorno) -> str:
    """La búsqueda lanza al consultar (los embeddings fallan tras el arranque)."""

    def embeber(textos):
        raise ErrorDeBusqueda(f"{MARCA_MENSAJE}: {textos!r} SELECT * FROM fragmentos")

    entorno.embeddings.embeber = embeber
    return "ErrorDeBusqueda"


def _falla_insert(entorno) -> str:
    """El INSERT de `consultas` falla (D10): la tabla ya no existe."""
    con = sqlite3.connect(entorno.ruta_sqlite)
    con.execute("DROP TABLE consultas")
    con.commit()
    con.close()
    return "OperationalError"


FALLOS = {"busqueda": _falla_busqueda, "insert": _falla_insert}


@pytest.fixture(params=sorted(FALLOS))
def fallo(request, arrancar, entorno, caplog):
    """Entrega una función que arranca la app, provoca el fallo y consulta.

    Devuelve (escenario, respuesta, tipo). Se ejecuta en el cuerpo de la prueba: `caplog` solo
    conserva los registros de la fase en curso.
    """

    def provocar():
        caplog.set_level(logging.DEBUG)
        with arrancar() as cliente:
            tipo = FALLOS[request.param](entorno)
            respuesta = cliente.post(RUTA, json={"pregunta": PREGUNTA})
        return request.param, respuesta, tipo

    return provocar


def test_s13_1_la_busqueda_que_lanza_responde_500_problem_json_con_request_id_y_detail_generico(
    arrancar, entorno
):
    with arrancar() as cliente:
        _falla_busqueda(entorno)
        respuesta = cliente.post(RUTA, json={"pregunta": PREGUNTA})

    assert respuesta.status_code == 500
    assert respuesta.headers["content-type"].startswith("application/problem+json")
    cuerpo = respuesta.json()
    assert set(cuerpo) == {"type", "title", "status", "detail", "requestId"}
    assert cuerpo["status"] == 500
    assert cuerpo["requestId"] == respuesta.headers["X-Request-Id"]
    assert cuerpo["detail"] == DETALLE_GENERICO
    assert entorno.redactor.llamadas == []  # falló antes de redactar
    assert entorno.filas() == []  # sin respuesta no hay registro


def test_s13_1_c1_el_cuerpo_del_500_no_lleva_trazas_rutas_sql_ni_la_pregunta(fallo):
    escenario, respuesta, _ = fallo()

    assert respuesta.status_code == 500, escenario
    for prohibido in PROHIBIDOS_EN_CUERPO:
        assert prohibido not in respuesta.text, f"{escenario}: el cuerpo expone {prohibido!r}"
    assert respuesta.json()["detail"] == DETALLE_GENERICO
    assert "ErrorDeBusqueda" not in respuesta.text and "OperationalError" not in respuesta.text


def test_s11_2_si_falla_el_insert_de_consultas_responde_el_mismo_500_generico(arrancar, entorno):
    with arrancar() as cliente:
        _falla_insert(entorno)
        respuesta = cliente.post(RUTA, json={"pregunta": PREGUNTA})

    assert respuesta.status_code == 500
    assert respuesta.headers["content-type"].startswith("application/problem+json")
    cuerpo = respuesta.json()
    assert cuerpo["detail"] == DETALLE_GENERICO
    assert cuerpo["requestId"] == respuesta.headers["X-Request-Id"]
    assert "Respuesta del doble." not in respuesta.text  # D10: sin registro no hay respuesta


def test_nfr4_el_log_del_500_lleva_request_id_y_tipo_de_error_sin_pregunta_ni_mensaje(
    fallo, caplog, linea_json
):
    escenario, respuesta, tipo = fallo()
    request_id = respuesta.json()["requestId"]

    linea = linea_json(request_id)
    assert linea is not None, f"{escenario}: no hay línea de log con el requestId"
    assert linea["codigo"] == 500
    assert linea["error"] == tipo
    assert MARCA_PREGUNTA not in caplog.text and PREGUNTA not in caplog.text
    assert MARCA_MENSAJE not in caplog.text  # el mensaje de la excepción puede traer PII
    assert "SELECT" not in caplog.text and "Traceback" not in caplog.text
    con_id = [r for r in caplog.records if request_id in r.getMessage()]
    assert len(con_id) == 1, f"{escenario}: se esperaba una sola línea con el requestId"
