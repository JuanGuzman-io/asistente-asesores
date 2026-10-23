"""T9 (MDO-0001) API `POST /api/consultar`: contrato, validación 422, 500, log JSON, SQLite.

Traza: S-14.1 y AC-3 (contrato 200), S-7.1/C1 y S-7.1 (422 de forma), S-7.2, S-7.2/C1 y S-7.2/C2
(límite de 1.000 puntos de código), S-11.1/C1 (422 sin filas), NFR-4 (log JSON sin PII), tabla ACID
(conexión por petición, WAL, `crear_esquema` al arrancar), pendientes de revisión (modo por petición
y handler de 500 sin PII).

API asumida (ver `conftest.py`): `crear_app(..., redactor=<doble>)`; la ruta es `POST /api/consultar`
con `{"pregunta": str}`. Respuestas de error con `application/problem+json` y campos `type`, `title`,
`status`, `detail`, `requestId`; `X-Request-Id` en toda respuesta (UUID v4, igual a `requestId`).
Log JSON por petición (módulo `logging`, nivel INFO, cualquier logger, un mensaje que es un objeto
JSON): `requestId`, `codigo` (HTTP, entero), `latenciaMs` (número >= 0), `fuentes` (entero) y, en 200,
`estado` (texto del contrato). La pregunta nunca aparece en logs.
"""

import logging
import sqlite3
import threading
import unicodedata
import uuid
from collections.abc import Sequence
from concurrent.futures import ThreadPoolExecutor

import pytest

from src.server.dominio.modelos import Fragmento
from src.server.dominio.puertos import RespuestaRedactada
from src.server.infraestructura.redactor.extractivo import RedactorExtractivo

RUTA = "/api/consultar"
PREGUNTA_VALIDA = "¿Cuál es el monto máximo del Crédito Productivo Impulso?"
CAMPOS_PROBLEMA = {"type", "title", "status", "detail", "requestId"}


def _es_uuid4(valor: str) -> bool:
    return uuid.UUID(valor).version == 4


def _afirmar_problema(respuesta, codigo: int) -> dict:
    assert respuesta.status_code == codigo
    assert respuesta.headers["content-type"].startswith("application/problem+json")
    cuerpo = respuesta.json()
    assert CAMPOS_PROBLEMA <= set(cuerpo)
    assert cuerpo["status"] == codigo
    assert isinstance(cuerpo["detail"], str) and cuerpo["detail"].strip()
    assert cuerpo["requestId"] == respuesta.headers["X-Request-Id"]
    assert _es_uuid4(cuerpo["requestId"])
    return cuerpo


def _sin_efectos(entorno) -> None:
    """Rechazada: no consultó documentos (ni embeddings ni redactor) y no registró nada."""
    assert entorno.embeddings.textos == []
    assert entorno.redactor.llamadas == []
    assert entorno.filas() == []


# --- S-14.1 y AC-3 -----------------------------------------------------------------------------


def test_s14_1_consulta_valida_responde_200_con_exactamente_respuesta_fuentes_estado(
    cliente, entorno
):
    respuesta = cliente.post(RUTA, json={"pregunta": PREGUNTA_VALIDA})

    assert respuesta.status_code == 200
    assert respuesta.headers["content-type"].startswith("application/json")
    cuerpo = respuesta.json()
    assert set(cuerpo) == {"respuesta", "fuentes", "estado"}
    assert cuerpo["respuesta"] == "Respuesta del doble."
    assert cuerpo["estado"] == "Exitosa"
    assert len(cuerpo["fuentes"]) >= 1
    for fuente in cuerpo["fuentes"]:
        assert set(fuente) == {"documento", "seccion", "fragmento"}
        assert all(isinstance(v, str) and v for v in fuente.values())


def test_s14_1_la_respuesta_lleva_x_request_id_uuid_v4_distinto_en_cada_peticion(cliente):
    a = cliente.post(RUTA, json={"pregunta": PREGUNTA_VALIDA})
    b = cliente.post(RUTA, json={"pregunta": PREGUNTA_VALIDA})

    assert _es_uuid4(a.headers["X-Request-Id"])
    assert _es_uuid4(b.headers["X-Request-Id"])
    assert a.headers["X-Request-Id"] != b.headers["X-Request-Id"]


def test_ac3_monto_maximo_del_credito_impulso_cita_el_documento_con_el_monto_que_dice(arrancar):
    with arrancar(redactor=RedactorExtractivo()) as cliente:
        respuesta = cliente.post(RUTA, json={"pregunta": PREGUNTA_VALIDA})

    cuerpo = respuesta.json()
    assert respuesta.status_code == 200
    assert cuerpo["estado"] == "Exitosa"
    assert "$50.000.000" in cuerpo["respuesta"]
    assert any(
        unicodedata.normalize("NFC", f["documento"]) == "Productos de Crédito"
        and f["seccion"] == "Crédito Productivo Impulso"
        for f in cuerpo["fuentes"]
    )


def test_s14_1_una_consulta_valida_queda_registrada_con_el_request_id_de_la_cabecera(
    cliente, entorno
):
    respuesta = cliente.post(RUTA, json={"pregunta": PREGUNTA_VALIDA})

    (fila,) = entorno.filas()
    assert fila["request_id"] == respuesta.headers["X-Request-Id"]
    assert fila["pregunta"] == PREGUNTA_VALIDA
    assert fila["estado"] == "EXITOSA"
    assert fila["modo"] == "modelo"


def test_una_ruta_inexistente_o_con_metodo_no_permitido_responde_problema_con_request_id(cliente):
    _afirmar_problema(cliente.get(RUTA), 405)
    _afirmar_problema(cliente.get("/api/no-existe"), 404)


# --- S-7.1 -------------------------------------------------------------------------------------

CUERPOS_INVALIDOS = {
    "vacia": b'{"pregunta": ""}',
    "solo_espacios": b'{"pregunta": "   "}',
    "solo_espacios_unicode": b'{"pregunta": "\\u00a0\\t\\n \\u2003"}',
    "sin_pregunta": b"{}",
    "pregunta_numero": b'{"pregunta": 5}',
    "pregunta_nula": b'{"pregunta": null}',
    "pregunta_lista": b'{"pregunta": ["a"]}',
    "cuerpo_no_objeto": b'["pregunta"]',
    "json_mal_formado": b'{"pregunta": "hola',
    "cuerpo_vacio": b"",
}


@pytest.mark.parametrize("cuerpo", CUERPOS_INVALIDOS.values(), ids=CUERPOS_INVALIDOS.keys())
def test_s7_1_cuerpo_invalido_responde_422_problema_sin_consultar_ni_registrar(
    cliente, entorno, cuerpo
):
    respuesta = cliente.post(RUTA, content=cuerpo, headers={"Content-Type": "application/json"})

    _afirmar_problema(respuesta, 422)
    _sin_efectos(entorno)


# --- S-7.2 -------------------------------------------------------------------------------------


def _mil() -> str:
    """Exactamente 1.000 caracteres, sin espacios en los extremos."""
    return ("monto maximo credito impulso " * 40)[:999] + "x"


def test_s7_2_1001_puntos_de_codigo_responde_422_con_el_limite_sin_consultar_ni_registrar(
    cliente, entorno
):
    pregunta = _mil() + "x"
    assert len(pregunta) == 1001

    respuesta = cliente.post(RUTA, json={"pregunta": pregunta})

    cuerpo = _afirmar_problema(respuesta, 422)
    assert "1.000" in cuerpo["detail"] or "1000" in cuerpo["detail"]
    _sin_efectos(entorno)


def test_s7_2_1001_tras_quitar_espacios_exteriores_tambien_se_rechaza(cliente, entorno):
    pregunta = "   " + _mil() + "x" + "\n  "

    respuesta = cliente.post(RUTA, json={"pregunta": pregunta})

    _afirmar_problema(respuesta, 422)
    _sin_efectos(entorno)


def test_s7_2_1001_en_nfc_enviada_en_nfd_con_mas_puntos_de_codigo_se_rechaza(cliente, entorno):
    pregunta = unicodedata.normalize("NFD", "é" * 400 + "x" * 601)
    assert len(unicodedata.normalize("NFC", pregunta)) == 1001

    respuesta = cliente.post(RUTA, json={"pregunta": pregunta})

    _afirmar_problema(respuesta, 422)
    _sin_efectos(entorno)


def _casos_mil() -> dict[str, tuple[str, str]]:
    exacta = _mil()
    nfc = "é" * 400 + "x" * 600
    return {
        "exactamente_1000": (exacta, exacta),
        "1000_con_espacios_exteriores": ("   " + exacta + " \n\t", exacta),
        "nfd_que_queda_en_1000_al_normalizar": (unicodedata.normalize("NFD", nfc), nfc),
    }


@pytest.mark.parametrize("caso", _casos_mil().values(), ids=_casos_mil().keys())
def test_s7_2_c1_mil_puntos_de_codigo_tras_normalizar_se_procesa_con_la_pregunta_normalizada(
    cliente, entorno, caso
):
    enviada, esperada = caso
    assert len(esperada) == 1000

    respuesta = cliente.post(RUTA, json={"pregunta": enviada})

    assert respuesta.status_code == 200
    assert respuesta.json()["estado"] == "Exitosa"
    # Se procesó y registró la forma NFC sin espacios exteriores, entera: sin recortar.
    assert entorno.redactor.llamadas == [esperada]
    (fila,) = entorno.filas()
    assert fila["pregunta"] == esperada


# --- La tabla existe desde el arranque, en WAL -------------------------------------------------


def test_el_arranque_crea_la_tabla_consultas_vacia_con_wal(cliente, entorno):
    con = sqlite3.connect(entorno.ruta_sqlite)
    try:
        modo = con.execute("PRAGMA journal_mode").fetchone()[0]
        version = con.execute("PRAGMA user_version").fetchone()[0]
        tabla = con.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='consultas'"
        ).fetchall()
    finally:
        con.close()
    assert tabla == [("consultas",)]
    assert version == 1
    assert modo == "wal"  # tabla ACID: WAL; escrituras serializadas por SQLite
    assert entorno.filas() == []


# --- Tabla ACID: una conexión SQLite por petición ----------------------------------------------


def _espiar_conexiones(monkeypatch, ruta_sqlite):
    real = sqlite3.connect
    abiertas: list[tuple[sqlite3.Connection, dict]] = []

    def espia(base, *args, **kwargs):
        con = real(base, *args, **kwargs)
        if str(base) == str(ruta_sqlite):  # Qdrant local también usa sqlite3: se filtra por ruta
            abiertas.append((con, kwargs))
        return con

    monkeypatch.setattr(sqlite3, "connect", espia)
    return abiertas


def _cerrada(con: sqlite3.Connection) -> bool:
    try:
        con.execute("SELECT 1")
    except sqlite3.ProgrammingError:
        return True
    return False


def test_acid_cada_peticion_abre_su_propia_conexion_sqlite_y_la_cierra(
    arrancar, entorno, monkeypatch
):
    abiertas = _espiar_conexiones(monkeypatch, entorno.ruta_sqlite)

    with arrancar() as cliente:
        tras_arranque = len(abiertas)
        cliente.post(RUTA, json={"pregunta": PREGUNTA_VALIDA})
        tras_primera = len(abiertas)
        assert tras_primera > tras_arranque
        assert all(_cerrada(con) for con, _ in abiertas[tras_arranque:])  # cerradas al responder
        cliente.post(RUTA, json={"pregunta": PREGUNTA_VALIDA})
        assert len(abiertas) > tras_primera
        assert all(_cerrada(con) for con, _ in abiertas[tras_primera:])

    primera = {id(con) for con, _ in abiertas[tras_arranque:tras_primera]}
    segunda = {id(con) for con, _ in abiertas[tras_primera:]}
    assert primera.isdisjoint(segunda)  # ninguna conexión se comparte entre peticiones
    assert all(kw.get("check_same_thread", True) is not False for _, kw in abiertas)


# --- Pendiente: `modo` por petición con peticiones concurrentes --------------------------------


class RedactorCarrera:
    """Como `RedactorGemini`: `modo` es estado de instancia que `redactar` escribe.

    ALFA pasa al extractivo; BETA usa el modelo. Fuerza la intercalación que corrompe un `modo`
    compartido: ALFA escribe, BETA escribe, ALFA retorna. Si la app serializa o aísla por petición,
    las esperas vencen por tiempo (1 s) y cada una conserva su modo.
    """

    modo = "modelo"

    def __init__(self) -> None:
        self.alfa_escribio = threading.Event()
        self.beta_escribio = threading.Event()

    def redactar(self, pregunta: str, fragmentos: Sequence[Fragmento]) -> RespuestaRedactada:
        if "ALFA" in pregunta:
            self.modo = "extractivo"
            self.alfa_escribio.set()
            self.beta_escribio.wait(1.0)
        else:
            self.alfa_escribio.wait(1.0)
            self.modo = "modelo"
            self.beta_escribio.set()
        return RespuestaRedactada("Respuesta de la carrera.", [1])


def test_dos_peticiones_concurrentes_registran_cada_una_su_propio_modo(arrancar, entorno):
    pregunta_alfa = "ALFA monto maximo del credito impulso"
    pregunta_beta = "BETA monto maximo del credito impulso"

    with arrancar(redactor=RedactorCarrera()) as cliente:
        with ThreadPoolExecutor(max_workers=2) as pool:
            alfa = pool.submit(cliente.post, RUTA, json={"pregunta": pregunta_alfa})
            beta = pool.submit(cliente.post, RUTA, json={"pregunta": pregunta_beta})
            assert alfa.result().status_code == 200
            assert beta.result().status_code == 200

    modos = {fila["pregunta"]: fila["modo"] for fila in entorno.filas()}
    assert modos == {pregunta_alfa: "extractivo", pregunta_beta: "modelo"}


# --- Pendiente: el handler de 500 no registra la pregunta ni `repr(resultado)` -----------------

SECRETO = "cliente-Zeta-4821"  # pragma: allowlist secret


class RedactorQueFalla:
    modo = "modelo"

    def redactar(self, pregunta: str, fragmentos: Sequence[Fragmento]) -> RespuestaRedactada:
        raise RuntimeError(f"fallo interno con la pregunta: {pregunta}")


def test_500_inesperado_responde_problema_sin_detalles_y_sin_la_pregunta_en_logs(
    arrancar, entorno, caplog, linea_json
):
    caplog.set_level(logging.DEBUG)
    pregunta = f"{SECRETO} monto maximo del credito impulso"

    with arrancar(redactor=RedactorQueFalla()) as cliente:
        respuesta = cliente.post(RUTA, json={"pregunta": pregunta})

    cuerpo = _afirmar_problema(respuesta, 500)
    assert SECRETO not in respuesta.text
    assert "RuntimeError" not in respuesta.text and "Traceback" not in respuesta.text
    assert SECRETO not in caplog.text  # ni mensaje de excepción ni traza ni la pregunta
    assert "Resultado(" not in caplog.text
    assert entorno.filas() == []
    linea = linea_json(cuerpo["requestId"])
    assert linea is not None and linea["codigo"] == 500


def test_500_por_fallo_al_registrar_no_deja_pregunta_ni_resultado_en_logs(
    arrancar, entorno, caplog
):
    caplog.set_level(logging.DEBUG)
    pregunta = f"{SECRETO} monto maximo del credito impulso"

    with arrancar() as cliente:
        con = sqlite3.connect(entorno.ruta_sqlite)
        con.execute("DROP TABLE consultas")  # el INSERT de D10 fallará con un error de SQLite
        con.commit()
        con.close()
        respuesta = cliente.post(RUTA, json={"pregunta": pregunta})

    _afirmar_problema(respuesta, 500)  # D10: sin registro no hay respuesta
    assert "Respuesta del doble." not in respuesta.text
    assert "consultas" not in respuesta.text and "sqlite" not in respuesta.text.lower()
    assert SECRETO not in caplog.text
    assert "Resultado(" not in caplog.text  # repr(resultado) lleva respuesta y fuentes
    assert "Respuesta del doble." not in caplog.text


# --- NFR-4: una línea JSON por petición, sin la pregunta ---------------------------------------


def test_nfr4_cada_peticion_valida_emite_una_linea_json_sin_el_texto_de_la_pregunta(
    cliente, caplog, linea_json
):
    caplog.set_level(logging.INFO)
    pregunta = f"{SECRETO} monto maximo del credito impulso"

    respuesta = cliente.post(RUTA, json={"pregunta": pregunta})

    linea = linea_json(respuesta.headers["X-Request-Id"])
    assert linea is not None
    assert linea["codigo"] == 200
    assert linea["estado"] == "Exitosa"
    assert linea["fuentes"] == len(respuesta.json()["fuentes"]) >= 1
    assert isinstance(linea["latenciaMs"], int | float) and linea["latenciaMs"] >= 0
    assert SECRETO not in caplog.text
    assert pregunta not in caplog.text


def test_nfr4_una_peticion_rechazada_emite_su_linea_json_sin_el_texto_de_la_pregunta(
    cliente, caplog, linea_json
):
    caplog.set_level(logging.DEBUG)
    pregunta = f"{SECRETO} " + "x" * 1001

    respuesta = cliente.post(RUTA, json={"pregunta": pregunta})

    linea = linea_json(respuesta.headers["X-Request-Id"])
    assert respuesta.status_code == 422
    assert linea is not None
    assert linea["codigo"] == 422
    assert linea["fuentes"] == 0
    assert isinstance(linea["latenciaMs"], int | float)
    assert SECRETO not in caplog.text  # tampoco por los errores de validación de Pydantic
