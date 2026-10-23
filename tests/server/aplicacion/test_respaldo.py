"""T11 (MDO-0001): si Gemini falla, tarda o no está configurado, la respuesta es extractiva (AC-16).

Traza: S-12.1 (error y tiempo agotado del cliente) y S-12.2 (sin `GEMINI_API_KEY` no se crea el
cliente), D9 (`HttpOptions(timeout=5000)` sin `retry_options`, un solo intento) y D12.
Sin red: dobles del cliente y espía de `genai.Client`.
"""

import json
from types import SimpleNamespace
from typing import Any

import httpx
import pytest
from google.genai import errors as genai_errors

from src.server.aplicacion.consultar import consultar
from src.server.dominio.estados import Estado
from src.server.dominio.modelos import Fragmento
from src.server.dominio.puertos import ResultadoBusqueda
from src.server.infraestructura.redactor import gemini
from src.server.infraestructura.redactor.gemini import RedactorGemini

IMPULSO = Fragmento(
    "Productos de Crédito", "Crédito Productivo Impulso", "Monto máximo de $50.000.000."
)
CONDICIONES = Fragmento("Productos de Crédito", "Condiciones", "Plazo de hasta 36 meses.")
PREGUNTA = "¿Cuál es el monto máximo del Crédito Productivo Impulso?"
ENCABEZADO = "Esto es lo que encontré en la base documental:"


class BuscadorDoble:
    def buscar(self, pregunta: str) -> ResultadoBusqueda:
        return ResultadoBusqueda(fragmentos=[IMPULSO, CONDICIONES], hay_soporte=True)


class RepositorioDoble:
    def __init__(self) -> None:
        self.registros: list[dict[str, Any]] = []

    def registrar(self, *, request_id: str, pregunta: str, resultado: Any, modo: str) -> None:
        self.registros.append({"pregunta": pregunta, "resultado": resultado, "modo": modo})


class ClienteCaido:
    """Doble del cliente `genai`: `models.generate_content` lanza `error`."""

    def __init__(self, error: Exception) -> None:
        self.llamadas = 0
        self.models = self
        self._error = error

    def generate_content(self, **_: object) -> object:
        self.llamadas += 1
        raise self._error


class ClienteSecuencial:
    """Doble del cliente `genai`: cada llamada devuelve un texto (JSON) o lanza una excepción."""

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


class FabricaDoble:
    def __init__(self, cliente: ClienteCaido) -> None:
        self.cliente = cliente
        self.claves: list[str] = []

    def __call__(self, api_key: str) -> ClienteCaido:
        self.claves.append(api_key)
        return self.cliente


def _consultar(redactor: RedactorGemini) -> tuple[Any, RepositorioDoble]:
    repo = RepositorioDoble()
    resultado = consultar(PREGUNTA, buscador=BuscadorDoble(), redactor=redactor, repositorio=repo)
    return resultado, repo


def _afirmar_extractiva(resultado: Any, repo: RepositorioDoble) -> None:
    assert resultado.estado == Estado.EXITOSA
    assert resultado.respuesta.startswith(ENCABEZADO)
    assert "$50.000.000" in resultado.respuesta
    assert [(f.documento, f.seccion) for f in resultado.fuentes] == [
        ("Productos de Crédito", "Crédito Productivo Impulso"),
        ("Productos de Crédito", "Condiciones"),
    ]
    assert all(f.fragmento for f in resultado.fuentes)
    (registro,) = repo.registros
    assert registro["modo"] == "extractivo"
    assert registro["resultado"] == resultado


@pytest.mark.parametrize(
    "error",
    [
        RuntimeError("503 del servicio"),
        ConnectionError("sin red"),
        ValueError("raro"),
        # Errores reales del transporte y del SDK: no heredan de OSError ni de RuntimeError.
        httpx.ReadTimeout("timeout de lectura"),
        httpx.ConnectTimeout("timeout de conexión"),
        httpx.TimeoutException("timeout"),
        genai_errors.APIError(500, {"error": {"message": "fallo", "status": "INTERNAL"}}),
        genai_errors.ServerError(
            503, {"error": {"message": "no disponible", "status": "UNAVAILABLE"}}
        ),
        genai_errors.ClientError(
            429, {"error": {"message": "cuota", "status": "RESOURCE_EXHAUSTED"}}
        ),
    ],
    ids=[
        "RuntimeError",
        "ConnectionError",
        "ValueError",
        "httpx.ReadTimeout",
        "httpx.ConnectTimeout",
        "httpx.TimeoutException",
        "genai.APIError",
        "genai.ServerError",
        "genai.ClientError",
    ],
)
def test_s12_1_con_el_cliente_lanzando_error_responde_exitosa_extractiva_y_registra_extractivo(
    error,
):
    cliente = ClienteCaido(error)
    redactor = RedactorGemini(api_key="clave-falsa", fabrica_cliente=FabricaDoble(cliente))

    resultado, repo = _consultar(redactor)

    _afirmar_extractiva(resultado, repo)
    assert cliente.llamadas == 1  # D9: un solo intento, sin reintentos


def test_s12_1_con_el_cliente_que_agota_el_tiempo_responde_exitosa_extractiva_y_registra_extractivo():
    cliente = ClienteCaido(TimeoutError("timeout de 5 s"))
    redactor = RedactorGemini(api_key="clave-falsa", fabrica_cliente=FabricaDoble(cliente))

    resultado, repo = _consultar(redactor)

    _afirmar_extractiva(resultado, repo)
    assert cliente.llamadas == 1


def test_s12_1_el_modo_registrado_sigue_a_cada_consulta_modelo_y_luego_extractivo():
    """Una caída tras un éxito debe registrar `extractivo`: el `modo` no puede quedar rancio."""
    cliente = ClienteSecuencial(SALIDA_VALIDA, genai_errors.ServerError(503, {"error": {}}))
    redactor = RedactorGemini(api_key="clave-falsa", fabrica_cliente=lambda _: cliente)
    repo = RepositorioDoble()

    for _ in range(2):  # misma instancia del redactor compartido
        consultar(PREGUNTA, buscador=BuscadorDoble(), redactor=redactor, repositorio=repo)

    assert [r["modo"] for r in repo.registros] == ["modelo", "extractivo"]
    assert repo.registros[0]["resultado"].respuesta == "El monto máximo es de $50.000.000."
    assert repo.registros[1]["resultado"].respuesta.startswith(ENCABEZADO)
    assert cliente.llamadas == 2


def test_s12_1_si_la_fabrica_del_cliente_falla_responde_extractiva_y_registra_extractivo():
    def fabrica(_: str) -> object:
        raise RuntimeError("no se pudo crear el cliente")

    resultado, repo = _consultar(RedactorGemini(api_key="clave-falsa", fabrica_cliente=fabrica))

    _afirmar_extractiva(resultado, repo)


def test_s12_1_el_error_del_cliente_no_se_propaga_ni_filtra_la_clave_o_la_pregunta(caplog):
    cliente = ClienteCaido(RuntimeError(f"fallo con clave-secreta y {PREGUNTA}"))
    redactor = RedactorGemini(api_key="clave-secreta", fabrica_cliente=FabricaDoble(cliente))

    with caplog.at_level("DEBUG"):
        resultado, _ = _consultar(redactor)

    assert resultado.estado == Estado.EXITOSA
    assert "clave-secreta" not in caplog.text
    assert PREGUNTA not in caplog.text


@pytest.mark.parametrize("clave", [None, ""])
def test_s12_2_sin_clave_no_se_llama_a_la_fabrica_y_la_respuesta_es_extractiva(clave):
    fabrica = FabricaDoble(ClienteCaido(RuntimeError("no debe llamarse")))
    redactor = RedactorGemini(api_key=clave, fabrica_cliente=fabrica)

    resultado, repo = _consultar(redactor)

    assert fabrica.claves == []
    assert fabrica.cliente.llamadas == 0
    _afirmar_extractiva(resultado, repo)


def test_s12_2_sin_clave_la_fabrica_por_defecto_no_crea_genai_client(monkeypatch):
    from google import genai

    creados: list[object] = []
    monkeypatch.setattr(genai, "Client", lambda *a, **k: creados.append((a, k)))

    resultado, repo = _consultar(RedactorGemini(api_key=None))

    assert creados == []
    _afirmar_extractiva(resultado, repo)


def test_d9_la_fabrica_por_defecto_usa_httpoptions_timeout_5000_y_sin_retry_options(monkeypatch):
    from google import genai

    capturado: dict[str, Any] = {}

    class ClienteEspia:
        def __init__(self, *args: object, **kwargs: Any) -> None:
            capturado["kwargs"] = kwargs

    monkeypatch.setattr(genai, "Client", ClienteEspia)

    gemini._fabrica_por_defecto("clave-falsa")

    opciones = capturado["kwargs"]["http_options"]
    assert capturado["kwargs"]["api_key"] == "clave-falsa"
    assert opciones.timeout == 5000
    assert gemini.TIMEOUT_MS == 5000
    assert opciones.retry_options is None


def test_d9_el_cliente_real_creado_por_la_fabrica_queda_con_timeout_5000_y_sin_reintentos():
    cliente = gemini._fabrica_por_defecto("clave-falsa")  # no hace llamadas de red

    # OJO: depende de atributos privados del SDK (`_api_client._http_options`); si una versión de
    # google-genai los renombra, esta prueba falla por el SDK y no por el producto. No hay API
    # pública para leer el timeout configurado; el espía de arriba cubre D9 sin ese acoplamiento.
    opciones = cliente._api_client._http_options
    assert opciones.timeout == 5000
    assert opciones.retry_options is None
