from dataclasses import dataclass

from src.server.dominio.estados import Estado


@dataclass(frozen=True)
class Fragmento:
    documento: str
    seccion: str
    texto: str


@dataclass(frozen=True)
class Fuente:
    documento: str
    seccion: str
    fragmento: str


@dataclass(frozen=True)
class Resultado:
    respuesta: str
    fuentes: list[Fuente]
    estado: Estado
