from dataclasses import dataclass


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
