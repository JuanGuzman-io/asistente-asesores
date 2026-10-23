from src.server.dominio.estados import Estado
from src.server.dominio.modelos import Resultado
from src.server.dominio.puertos import BuscadorDocumental, Redactor
from src.server.dominio.reglas import MENSAJE_SIN_INFORMACION, deduplicar_fuentes


def consultar(pregunta: str, *, buscador: BuscadorDocumental, redactor: Redactor) -> Resultado:
    busqueda = buscador.buscar(pregunta)
    if not busqueda.hay_soporte or not busqueda.fragmentos:
        return Resultado(MENSAJE_SIN_INFORMACION, [], Estado.SIN_INFORMACION)

    fragmentos = list(busqueda.fragmentos)
    redactada = redactor.redactar(pregunta, fragmentos)
    usados = set(redactada.fragmentos_usados)
    citados = [f for posicion, f in enumerate(fragmentos, start=1) if posicion in usados]
    return Resultado(redactada.respuesta, deduplicar_fuentes(citados), Estado.EXITOSA)
