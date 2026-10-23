from enum import StrEnum


class Estado(StrEnum):
    EXITOSA = "Exitosa"
    SIN_INFORMACION = "Sin información suficiente"
    BLOQUEADA = "Bloqueada por seguridad"


class CategoriaBloqueo(StrEnum):
    INFORMACION_RESTRINGIDA = "informacion_restringida"
    PROMPT_INJECTION = "prompt_injection"
    DATOS_DE_CLIENTES = "datos_de_clientes"
