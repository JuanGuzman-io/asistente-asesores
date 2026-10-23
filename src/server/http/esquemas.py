import unicodedata
from typing import Annotated

from pydantic import BaseModel, BeforeValidator

MAXIMO_PREGUNTA = 1000


def _normalizar(valor: object) -> object:
    if not isinstance(valor, str):
        return valor  # Pydantic lo rechaza como no texto
    texto = unicodedata.normalize("NFC", valor).strip()
    if not texto:
        raise ValueError("la pregunta no puede estar vacía")
    if len(texto) > MAXIMO_PREGUNTA:
        raise ValueError("la pregunta no puede superar 1.000 caracteres")
    return texto


class ConsultaEntrada(BaseModel):
    pregunta: Annotated[str, BeforeValidator(_normalizar)]


class FuenteSalida(BaseModel):
    documento: str
    seccion: str
    fragmento: str


class ConsultaSalida(BaseModel):
    respuesta: str
    fuentes: list[FuenteSalida]
    estado: str
