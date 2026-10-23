from dataclasses import dataclass


@dataclass(frozen=True)
class Fragmento:
    documento: str
    seccion: str
    texto: str
