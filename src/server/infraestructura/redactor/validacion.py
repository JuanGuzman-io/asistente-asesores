import re
from collections.abc import Sequence

from pydantic import BaseModel

from src.server.dominio.modelos import Fragmento
from src.server.dominio.puertos import RespuestaRedactada

# Cifra completa: dígitos con separadores de miles o decimales (`50.000`, `2,5`) y `%` pegado.
CIFRA = re.compile(r"\d+(?:[.,]\d+)*%?")


class SalidaModelo(BaseModel):
    """Esquema JSON que Gemini debe devolver (D7)."""

    respuesta: str
    # Posiciones 1-based en la lista numerada de fragmentos entregada al modelo.
    fragmentos_usados: list[int]
    partes_sin_soporte: list[str] = []


class SalidaInvalida(Exception):
    """La salida del modelo debe descartarse; los mensajes nunca llevan contenido (PII)."""


def validar_salida(salida: SalidaModelo, fragmentos: Sequence[Fragmento]) -> RespuestaRedactada:
    """Guardrail D7: ids recuperados, cifras respaldadas por los fragmentos citados (AC-4)."""
    if not salida.respuesta.strip():
        raise SalidaInvalida("respuesta vacía")
    if any(not 1 <= i <= len(fragmentos) for i in salida.fragmentos_usados):
        raise SalidaInvalida("id de fragmento no recuperado")
    if not salida.fragmentos_usados and not salida.partes_sin_soporte:
        raise SalidaInvalida("sin fragmentos usados ni partes sin soporte")

    citados = (fragmentos[i - 1].texto for i in set(salida.fragmentos_usados))
    respaldo = {cifra for texto in citados for cifra in CIFRA.findall(texto)}
    for texto in (salida.respuesta, *salida.partes_sin_soporte):
        if not set(CIFRA.findall(texto)) <= respaldo:
            raise SalidaInvalida("cifra ausente de los fragmentos citados")

    frases = [f"No encontré información sobre {parte}." for parte in salida.partes_sin_soporte]
    respuesta = " ".join([salida.respuesta.strip(), *frases])
    return RespuestaRedactada(
        respuesta=respuesta,
        fragmentos_usados=list(salida.fragmentos_usados),
        partes_sin_soporte=list(salida.partes_sin_soporte),
    )
