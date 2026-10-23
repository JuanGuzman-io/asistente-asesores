from enum import StrEnum


class Estado(StrEnum):
    EXITOSA = "Exitosa"
    SIN_INFORMACION = "Sin información suficiente"
    BLOQUEADA = "Bloqueada por seguridad"
