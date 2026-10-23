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
import time
import unicodedata
import uuid
from collections.abc import Sequence
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from src.server.config import DIRECTORIO_DATOS, DOCUMENTOS_EXCLUIDOS
from src.server.dominio.modelos import Fragmento
from src.server.dominio.puertos import RespuestaRedactada
from src.server.http.app import crear_app
from src.server.infraestructura.redactor.extractivo import RedactorExtractivo
from src.server.infraestructura.redactor.gemini import RedactorGemini

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


MENSAJE_VACIA = "La pregunta no puede estar vacía."
MENSAJE_LARGA = "La pregunta no puede superar los 1.000 caracteres."
MENSAJE_CUERPO = "El cuerpo debe ser un JSON con el campo pregunta de tipo texto."
FRASES_TECNICAS = ("La petición no es válida", "Value error", "pregunta:")

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


MENSAJES_422 = {
    "vacia": MENSAJE_VACIA,
    "solo_espacios": MENSAJE_VACIA,
    "sin_pregunta": MENSAJE_CUERPO,
    "pregunta_numero": MENSAJE_CUERPO,
    "pregunta_nula": MENSAJE_CUERPO,
    "pregunta_lista": MENSAJE_CUERPO,
    "cuerpo_no_objeto": MENSAJE_CUERPO,
    "json_mal_formado": MENSAJE_CUERPO,
    "cuerpo_vacio": MENSAJE_CUERPO,
}


@pytest.mark.parametrize("nombre", MENSAJES_422)
def test_s7_1_el_422_responde_el_mensaje_fijo_exacto_de_su_causa(cliente, entorno, nombre):
    respuesta = cliente.post(
        RUTA, content=CUERPOS_INVALIDOS[nombre], headers={"Content-Type": "application/json"}
    )

    cuerpo = _afirmar_problema(respuesta, 422)
    assert cuerpo["detail"] == MENSAJES_422[nombre]
    _sin_efectos(entorno)


@pytest.mark.parametrize("cuerpo", CUERPOS_INVALIDOS.values(), ids=CUERPOS_INVALIDOS.keys())
def test_s7_1_c2_el_detail_del_422_no_lleva_texto_de_pydantic(cliente, cuerpo):
    respuesta = cliente.post(RUTA, content=cuerpo, headers={"Content-Type": "application/json"})

    detail = _afirmar_problema(respuesta, 422)["detail"]
    for frase in FRASES_TECNICAS:
        assert frase not in detail


@pytest.mark.parametrize(
    "cuerpo",
    [
        {"pregunta": ["texto-secreto-xyz"]},
        {"pregunta": {"texto-secreto-xyz": 1}},
        {"pregunta": "texto-secreto-xyz " + "x" * 1001},
        {"texto-secreto-xyz": "hola"},
    ],
    ids=["lista", "objeto", "demasiado_larga", "campo_desconocido"],
)
def test_s7_1_c2_el_detail_del_422_no_repite_el_texto_enviado(cliente, entorno, cuerpo):
    respuesta = cliente.post(RUTA, json=cuerpo)

    problema = _afirmar_problema(respuesta, 422)
    assert "texto-secreto-xyz" not in problema["detail"]
    for frase in FRASES_TECNICAS:
        assert frase not in problema["detail"]
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
    assert cuerpo["detail"] == MENSAJE_LARGA
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
            modo = self.modo = "extractivo"
            self.alfa_escribio.set()
            self.beta_escribio.wait(1.0)
        else:
            self.alfa_escribio.wait(1.0)
            modo = self.modo = "modelo"
            self.beta_escribio.set()
        # T15: el modo de cada llamada viaja en la respuesta; el atributo sigue corrompiéndose.
        return RespuestaRedactada("Respuesta de la carrera.", [1], modo=modo)


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


# --- T15 (D9, D13): llamadas al modelo en paralelo, limitadas por un semáforo -------------------
#
# Costuras que asumen estas pruebas (las sigue la implementación):
#   1. `crear_app(..., max_concurrencia: int | None = None)`: tope de llamadas simultáneas al
#      redactor. `None` lee la variable de entorno `GEMINI_MAX_CONCURRENCIA` (por defecto 5).
#      Sustituye al candado global `RedactorExclusivo`: las llamadas ya no se serializan.
#   2. `RespuestaRedactada` gana el campo opcional `modo: str | None = None`. Un redactor que lo
#      llena declara el modo de ESA llamada, y la ruta lo registra en `consultas.modo`: el
#      atributo de instancia `redactor.modo` es estado compartido y no se lee cuando la
#      respuesta trae `modo` (con varias llamadas simultáneas se corrompería).
#   3. Un 429 del SDK (`google.genai.errors.ClientError(429, ...)`) hace que `RedactorGemini` use
#      el extractivo y registre en el log el código 429 (solo el código, sin mensaje ni clave).

ESPERA_S = 0.3
BASE_PREGUNTA = "monto maximo del credito impulso"


class RedactorConcurrente:
    """Tarda `ESPERA_S`, mide el pico de llamadas simultáneas y declara el modo por llamada.

    Si la pregunta lleva EXTRACTIVO responde en modo extractivo; si no, en `modelo`. El atributo
    `modo` queda fijo en un valor engañoso: leerlo en lugar del modo de la respuesta falla.
    """

    modo = "modelo"

    def __init__(self, espera: float = ESPERA_S) -> None:
        self.espera = espera
        self._candado = threading.Lock()
        self.en_vuelo = 0
        self.pico = 0

    def redactar(self, pregunta: str, fragmentos: Sequence[Fragmento]) -> RespuestaRedactada:
        with self._candado:
            self.en_vuelo += 1
            self.pico = max(self.pico, self.en_vuelo)
        try:
            time.sleep(self.espera)
        finally:
            with self._candado:
                self.en_vuelo -= 1
        modo = "extractivo" if "EXTRACTIVO" in pregunta else "modelo"
        return RespuestaRedactada(f"Respuesta {modo}.", [1], modo=modo)


def _preguntas(n: int) -> list[str]:
    # Índices pares: modelo; impares: extractivo.
    return [f"{'EXTRACTIVO' if i % 2 else 'MODELO'} {i} {BASE_PREGUNTA}" for i in range(n)]


@contextmanager
def _app_concurrente(entorno, redactor, **opciones):
    app = crear_app(
        directorio_datos=DIRECTORIO_DATOS,
        excluidos=DOCUMENTOS_EXCLUIDOS,
        directorio_qdrant=entorno.directorio_qdrant,
        ruta_sqlite=entorno.ruta_sqlite,
        embeddings=entorno.embeddings,
        redactor=redactor,
        **opciones,
    )
    with TestClient(app, raise_server_exceptions=False) as cliente:
        cliente.post(RUTA, json={"pregunta": f"CALENTAMIENTO {BASE_PREGUNTA}"})
        yield cliente


def _disparar(cliente, preguntas):
    inicio = time.perf_counter()
    with ThreadPoolExecutor(max_workers=len(preguntas)) as pool:
        futuros = [pool.submit(cliente.post, RUTA, json={"pregunta": q}) for q in preguntas]
        respuestas = [f.result() for f in futuros]
    return respuestas, time.perf_counter() - inicio


def _afirmar_modos_por_peticion(entorno, preguntas, respuestas):
    esperado = {q: ("extractivo" if "EXTRACTIVO" in q else "modelo") for q in preguntas}
    assert all(r.status_code == 200 for r in respuestas)
    for q, r in zip(preguntas, respuestas, strict=True):
        assert r.json()["respuesta"] == f"Respuesta {esperado[q]}."  # el modo de su llamada
    filas = {f["pregunta"]: f for f in entorno.filas() if f["pregunta"] in esperado}
    assert {q: f["modo"] for q, f in filas.items()} == esperado
    for q, r in zip(preguntas, respuestas, strict=True):
        assert filas[q]["request_id"] == r.headers["X-Request-Id"]


def test_s12_1_cinco_consultas_con_modelo_no_se_serializan_y_cada_una_registra_su_modo(entorno):
    redactor = RedactorConcurrente()
    preguntas = _preguntas(5)

    with _app_concurrente(entorno, redactor) as cliente:  # límite por defecto: 5
        respuestas, _ = _disparar(cliente, preguntas)

    assert redactor.pico == 5
    _afirmar_modos_por_peticion(entorno, preguntas, respuestas)


def test_s12_1_con_mas_consultas_que_el_limite_nunca_hay_mas_en_vuelo_que_el_limite(entorno):
    redactor = RedactorConcurrente(espera=0.2)
    preguntas = _preguntas(5)

    with _app_concurrente(entorno, redactor, max_concurrencia=2) as cliente:
        respuestas, _ = _disparar(cliente, preguntas)

    assert redactor.pico == 2  # el semáforo limita a 2, y no serializa a 1
    _afirmar_modos_por_peticion(entorno, preguntas, respuestas)


def test_la_variable_gemini_max_concurrencia_fija_el_limite_cuando_no_se_pasa_parametro(
    entorno, monkeypatch
):
    monkeypatch.setenv("GEMINI_MAX_CONCURRENCIA", "2")
    redactor = RedactorConcurrente(espera=0.2)
    preguntas = _preguntas(5)

    with _app_concurrente(entorno, redactor) as cliente:
        respuestas, _ = _disparar(cliente, preguntas)

    assert redactor.pico == 2
    _afirmar_modos_por_peticion(entorno, preguntas, respuestas)


# --- S-12.1: 429 del API -> extractivo con 200 y el 429 en el log, sin contenido ----------------

CLAVE_429 = "AIzaSyFAKE-clave-429-no-debe-filtrarse"  # pragma: allowlist secret
MENSAJE_429 = "cuota agotada para el proyecto zeta-9917"


class _ModelosCon429:
    def generate_content(self, *, model, contents, config):
        from google.genai import errors

        raise errors.ClientError(
            429,
            {"error": {"code": 429, "status": "RESOURCE_EXHAUSTED", "message": MENSAJE_429}},
        )


def test_s12_1_un_429_del_api_responde_200_extractivo_y_el_log_lleva_el_429_sin_contenido(
    arrancar, entorno, caplog
):
    caplog.set_level(logging.DEBUG)
    cliente_sdk = SimpleNamespace(models=_ModelosCon429())
    redactor = RedactorGemini(api_key=CLAVE_429, fabrica_cliente=lambda clave: cliente_sdk)
    pregunta = f"{SECRETO} {BASE_PREGUNTA}"

    with arrancar(redactor=redactor) as cliente:
        respuesta = cliente.post(RUTA, json={"pregunta": pregunta})

    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert cuerpo["estado"] == "Exitosa"
    assert len(cuerpo["fuentes"]) >= 1
    (fila,) = entorno.filas()
    assert fila["modo"] == "extractivo"
    assert "429" in caplog.text  # solo el estado
    for prohibido in (pregunta, SECRETO, CLAVE_429, MENSAJE_429, "RESOURCE_EXHAUSTED"):
        assert prohibido not in caplog.text
