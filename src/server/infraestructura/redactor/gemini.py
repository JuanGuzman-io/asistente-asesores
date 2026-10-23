import logging
import re
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from src.server.dominio.modelos import Fragmento
from src.server.dominio.puertos import Redactor, RespuestaRedactada
from src.server.infraestructura.redactor.extractivo import RedactorExtractivo
from src.server.infraestructura.redactor.validacion import (
    SalidaInvalida,
    SalidaModelo,
    validar_salida,
)

logger = logging.getLogger(__name__)

MODELO = "gemini-3.5-flash-lite"
VERSION_PROMPT = "v1"
RUTA_PROMPT = Path(__file__).with_name("prompt.md")
TIMEOUT_MS = 5000  # D9: corte local de 5 s, un solo intento, sin reintentos
SERVER_TIMEOUT_S = 10  # el API rechaza plazos de servidor menores a 10 s
MODO_MODELO = "modelo"
MODO_EXTRACTIVO = "extractivo"

# Abre o cierra un delimitador: se neutraliza para que un texto no pueda cerrar su bloque (D5).
_ETIQUETA = re.compile(r"<(?=\s*/?\s*(?:fragmento|pregunta)\b)", re.IGNORECASE)


def _fabrica_por_defecto(api_key: str) -> Any:
    # Import diferido: el SDK es pesado y solo hace falta al crear el cliente real.
    from google import genai
    from google.genai import types

    opciones = types.HttpOptions(
        timeout=TIMEOUT_MS, headers={"X-Server-Timeout": str(SERVER_TIMEOUT_S)}
    )
    return genai.Client(api_key=api_key, http_options=opciones)


def _neutralizar(texto: str) -> str:
    return _ETIQUETA.sub("&lt;", texto)


def _armar_contenido(pregunta: str, fragmentos: Sequence[Fragmento]) -> str:
    bloques = [
        f'<fragmento id="{i}">\n{_neutralizar(f"{f.documento} > {f.seccion}")}\n'
        f"{_neutralizar(f.texto)}\n</fragmento>"
        for i, f in enumerate(fragmentos, start=1)
    ]
    bloques.append(f"<pregunta>\n{_neutralizar(pregunta)}\n</pregunta>")
    return "\n".join(bloques)


class RedactorGemini:
    """Redacta con Gemini y valida la salida (D7); ante cualquier fallo usa el extractivo (D9)."""

    modo: str = MODO_EXTRACTIVO

    def __init__(
        self,
        *,
        api_key: str | None,
        fabrica_cliente: Callable[[str], Any] | None = None,
        respaldo: Redactor | None = None,
    ) -> None:
        self._api_key = api_key
        self._fabrica = fabrica_cliente or _fabrica_por_defecto
        self._respaldo: Redactor = respaldo or RedactorExtractivo()
        self._cliente: Any = None

    def __repr__(self) -> str:
        return f"{type(self).__name__}(modelo={MODELO!r}, con_clave={bool(self._api_key)})"

    def redactar(self, pregunta: str, fragmentos: Sequence[Fragmento]) -> RespuestaRedactada:
        if not self._api_key:
            return self._respaldar("sin clave", pregunta, fragmentos)
        try:
            respuesta = validar_salida(self._llamar(pregunta, fragmentos), fragmentos)
        except SalidaInvalida:
            return self._respaldar("salida descartada por el guardrail", pregunta, fragmentos)
        except Exception as error:  # cualquier fallo pasa al extractivo (AC-16)
            # Solo el tipo: el mensaje del SDK puede traer la clave o la pregunta.
            return self._respaldar(
                f"fallo del modelo ({type(error).__name__})", pregunta, fragmentos
            )
        self.modo = MODO_MODELO
        return respuesta

    def _llamar(self, pregunta: str, fragmentos: Sequence[Fragmento]) -> SalidaModelo:
        if self._cliente is None:
            self._cliente = self._fabrica(self._api_key or "")
        respuesta = self._cliente.models.generate_content(
            model=MODELO,
            contents=_armar_contenido(pregunta, fragmentos),
            config={
                "system_instruction": RUTA_PROMPT.read_text(encoding="utf-8"),
                "response_mime_type": "application/json",
                "response_schema": SalidaModelo,
            },
        )
        try:
            return SalidaModelo.model_validate_json(respuesta.text)
        except (ValidationError, TypeError):
            # ValidationError incluye la entrada en su mensaje: se reemplaza por una sin contenido.
            raise SalidaInvalida("JSON o esquema inválido") from None

    def _respaldar(
        self, motivo: str, pregunta: str, fragmentos: Sequence[Fragmento]
    ) -> RespuestaRedactada:
        logger.warning("Redactor con modelo no disponible, se usa el extractivo: %s", motivo)
        self.modo = MODO_EXTRACTIVO
        return self._respaldo.redactar(pregunta, fragmentos)
