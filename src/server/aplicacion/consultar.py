import uuid

from src.server.dominio.estados import Estado
from src.server.dominio.modelos import Resultado
from src.server.dominio.puertos import BuscadorDocumental, Redactor, RepositorioConsultas
from src.server.dominio.reglas import MENSAJE_SIN_INFORMACION, deduplicar_fuentes

MODO_SIN_REDACCION = "ninguno"


def consultar(
    pregunta: str,
    *,
    buscador: BuscadorDocumental,
    redactor: Redactor,
    repositorio: RepositorioConsultas,
    request_id: str | None = None,
) -> Resultado:
    resultado, modo = _resolver(pregunta, buscador, redactor)
    # D10: se registra antes de devolver; si falla, el error se propaga y no hay respuesta.
    repositorio.registrar(
        request_id=request_id or str(uuid.uuid4()),
        pregunta=pregunta,
        resultado=resultado,
        modo=modo,
    )
    return resultado


def _resolver(
    pregunta: str, buscador: BuscadorDocumental, redactor: Redactor
) -> tuple[Resultado, str]:
    busqueda = buscador.buscar(pregunta)
    if not busqueda.hay_soporte or not busqueda.fragmentos:
        return Resultado(MENSAJE_SIN_INFORMACION, [], Estado.SIN_INFORMACION), MODO_SIN_REDACCION

    fragmentos = list(busqueda.fragmentos)
    redactada = redactor.redactar(pregunta, fragmentos)
    if not redactada.fragmentos_usados and redactada.partes_sin_soporte:
        # D7: el modelo declara que ninguna parte tiene soporte.
        sin_soporte = Resultado(MENSAJE_SIN_INFORMACION, [], Estado.SIN_INFORMACION)
        return sin_soporte, redactada.modo or redactor.modo
    usados = set(redactada.fragmentos_usados)
    citados = [f for posicion, f in enumerate(fragmentos, start=1) if posicion in usados]
    resultado = Resultado(redactada.respuesta, deduplicar_fuentes(citados), Estado.EXITOSA)
    return resultado, redactada.modo or redactor.modo
