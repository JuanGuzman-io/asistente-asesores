"""T5 (MDO-0001): el caso de uso `consultar` responde con fuentes o con el mensaje fijo (D4, D6).

API asumida (design.md nombra los puertos, `Estado`, `Resultado` y `MENSAJE_SIN_INFORMACION`,
pero no fija firmas):

    src/server/dominio/estados.py
        Estado(str, Enum): EXITOSA = "Exitosa", SIN_INFORMACION = "Sin información suficiente",
        BLOQUEADA = "Bloqueada por seguridad".
    src/server/dominio/reglas.py
        MENSAJE_SIN_INFORMACION = "No tengo información suficiente para responder."
    src/server/dominio/modelos.py
        Resultado(respuesta: str, fuentes: list[Fuente], estado: Estado)   (dataclass congelada)
    src/server/dominio/puertos.py
        RespuestaRedactada(respuesta: str, fragmentos_usados: Sequence[int])
            ids de los fragmentos que el redactor declara usados: posiciones 1-based en la lista
            numerada de fragmentos que se le entregó (D7: "fragmentos numerados").
        Redactor (Protocol): redactar(pregunta: str, fragmentos: Sequence[Fragmento])
            -> RespuestaRedactada
    src/server/aplicacion/consultar.py
        consultar(pregunta: str, *, buscador: BuscadorDocumental, redactor: Redactor) -> Resultado
            Sin soporte (hay_soporte False o sin fragmentos): mensaje fijo, sin fuentes, estado
            SIN_INFORMACION y sin llamar al redactor. Con soporte: llama al redactor, arma las
            fuentes con `deduplicar_fuentes` solo con los fragmentos declarados usados, estado
            EXITOSA. El registro (RepositorioConsultas, D10) queda fuera de T5.

S-6.1 es de nivel eval; se cubre aquí la parte determinista que el "Done when" de T5 pide
(forma de las fuentes, deduplicación y correspondencia con los fragmentos usados).
"""

from collections.abc import Sequence

from src.server.aplicacion.consultar import consultar
from src.server.dominio.estados import Estado
from src.server.dominio.modelos import Fragmento
from src.server.dominio.puertos import RespuestaRedactada, ResultadoBusqueda
from src.server.dominio.reglas import MENSAJE_SIN_INFORMACION

MENSAJE_FIJO = "No tengo información suficiente para responder."


class BuscadorDoble:
    def __init__(self, resultado: ResultadoBusqueda) -> None:
        self._resultado = resultado
        self.preguntas: list[str] = []

    def buscar(self, pregunta: str) -> ResultadoBusqueda:
        self.preguntas.append(pregunta)
        return self._resultado


class RedactorDoble:
    modo = "modelo"

    def __init__(
        self, usados: Sequence[int] = (1,), respuesta: str = "Respuesta redactada."
    ) -> None:
        self._respuesta = RespuestaRedactada(respuesta=respuesta, fragmentos_usados=usados)
        self.llamadas: list[tuple[str, Sequence[Fragmento]]] = []

    def redactar(self, pregunta: str, fragmentos: Sequence[Fragmento]) -> RespuestaRedactada:
        self.llamadas.append((pregunta, fragmentos))
        return self._respuesta


def _sin_soporte(fragmentos: Sequence[Fragmento] = ()) -> BuscadorDoble:
    return BuscadorDoble(ResultadoBusqueda(fragmentos=fragmentos, hay_soporte=False))


def _con_soporte(fragmentos: Sequence[Fragmento]) -> BuscadorDoble:
    return BuscadorDoble(ResultadoBusqueda(fragmentos=fragmentos, hay_soporte=True))


IMPULSO = Fragmento(
    "Productos de Crédito", "Crédito Productivo Impulso", "Monto de 1 a 20 millones."
)
CONDICIONES = Fragmento("Productos de Crédito", "Condiciones", "Plazo de hasta 36 meses.")
MICROSEGURO = Fragmento("Microseguros", "Cobertura", "Cubre muerte accidental.")


def test_s101_el_mensaje_fijo_es_exactamente_el_del_pdf():
    assert MENSAJE_SIN_INFORMACION == MENSAJE_FIJO


def test_s101_sin_soporte_responde_el_mensaje_fijo_sin_fuentes_y_con_estado_sin_informacion():
    redactor = RedactorDoble()

    resultado = consultar(
        "¿Cuál es la tasa de la hipoteca?",
        buscador=_sin_soporte(),
        repositorio=RepositorioDoble(),
        redactor=redactor,
    )

    assert resultado.respuesta == MENSAJE_FIJO
    assert resultado.fuentes == []
    assert resultado.estado == Estado.SIN_INFORMACION
    assert resultado.estado.value == "Sin información suficiente"


def test_s101_sin_soporte_no_llama_al_redactor():
    redactor = RedactorDoble()

    consultar(
        "¿Cuál es la tasa de la hipoteca?",
        buscador=_sin_soporte(),
        repositorio=RepositorioDoble(),
        redactor=redactor,
    )

    assert redactor.llamadas == []


def test_s101_bajo_el_umbral_con_fragmentos_candidatos_no_los_cita_ni_llama_al_redactor():
    redactor = RedactorDoble()
    buscador = _sin_soporte([IMPULSO])

    resultado = consultar(
        "pregunta lejana", buscador=buscador, repositorio=RepositorioDoble(), redactor=redactor
    )

    assert resultado.respuesta == MENSAJE_FIJO
    assert resultado.fuentes == []
    assert resultado.estado == Estado.SIN_INFORMACION
    assert redactor.llamadas == []


def test_s101_la_pregunta_llega_al_buscador_tal_cual():
    buscador = _sin_soporte()

    consultar(
        "¿Qué es Agro Crece?",
        buscador=buscador,
        repositorio=RepositorioDoble(),
        redactor=RedactorDoble(),
    )

    assert buscador.preguntas == ["¿Qué es Agro Crece?"]


def test_s102_base_vacia_responde_el_mensaje_fijo_sin_excepcion():
    redactor = RedactorDoble()

    resultado = consultar(
        "¿Qué créditos hay?",
        buscador=_sin_soporte([]),
        repositorio=RepositorioDoble(),
        redactor=redactor,
    )

    assert resultado.respuesta == MENSAJE_FIJO
    assert resultado.fuentes == []
    assert resultado.estado == Estado.SIN_INFORMACION
    assert redactor.llamadas == []


def test_s102_c1_base_vacia_con_soporte_declarado_sin_fragmentos_no_falla():
    # Un buscador inconsistente (hay_soporte sin fragmentos) tampoco debe romper (BUT NOT 5xx).
    redactor = RedactorDoble()
    buscador = BuscadorDoble(ResultadoBusqueda(fragmentos=[], hay_soporte=True))

    resultado = consultar(
        "¿Qué créditos hay?", buscador=buscador, repositorio=RepositorioDoble(), redactor=redactor
    )

    assert resultado.respuesta == MENSAJE_FIJO
    assert resultado.estado == Estado.SIN_INFORMACION
    assert redactor.llamadas == []


def test_s103_pregunta_ajena_a_los_cuatro_temas_es_sin_informacion():
    redactor = RedactorDoble()

    resultado = consultar(
        "¿Va a llover mañana en Bogotá?",
        buscador=_sin_soporte(),
        repositorio=RepositorioDoble(),
        redactor=redactor,
    )

    assert resultado.respuesta == MENSAJE_FIJO
    assert resultado.fuentes == []
    assert resultado.estado == Estado.SIN_INFORMACION
    assert redactor.llamadas == []


def test_s103_c1_pregunta_ajena_nunca_queda_bloqueada_por_seguridad():
    resultado = consultar(
        "¿Va a llover mañana en Bogotá?",
        buscador=_sin_soporte(),
        repositorio=RepositorioDoble(),
        redactor=RedactorDoble(),
    )

    assert resultado.estado != Estado.BLOQUEADA
    assert resultado.estado.value != "Bloqueada por seguridad"


def test_s61_con_soporte_responde_exitosa_con_la_respuesta_del_redactor():
    redactor = RedactorDoble(usados=[1], respuesta="Impulso financia de 1 a 20 millones.")

    resultado = consultar(
        "¿Cuánto financia Impulso?",
        buscador=_con_soporte([IMPULSO]),
        repositorio=RepositorioDoble(),
        redactor=redactor,
    )

    assert resultado.respuesta == "Impulso financia de 1 a 20 millones."
    assert resultado.estado == Estado.EXITOSA
    assert resultado.estado.value == "Exitosa"


def test_s61_el_redactor_recibe_la_pregunta_y_los_fragmentos_recuperados():
    redactor = RedactorDoble(usados=[1])

    consultar(
        "¿Cuánto financia Impulso?",
        buscador=_con_soporte([IMPULSO, CONDICIONES]),
        repositorio=RepositorioDoble(),
        redactor=redactor,
    )

    assert len(redactor.llamadas) == 1
    pregunta, fragmentos = redactor.llamadas[0]
    assert pregunta == "¿Cuánto financia Impulso?"
    assert list(fragmentos) == [IMPULSO, CONDICIONES]


def test_s61_cada_fuente_trae_documento_seccion_y_fragmento():
    resultado = consultar(
        "¿Cuánto financia Impulso?",
        buscador=_con_soporte([IMPULSO]),
        repositorio=RepositorioDoble(),
        redactor=RedactorDoble(usados=[1]),
    )

    assert len(resultado.fuentes) == 1
    fuente = resultado.fuentes[0]
    assert fuente.documento == "Productos de Crédito"
    assert fuente.seccion == "Crédito Productivo Impulso"
    assert fuente.fragmento == "Monto de 1 a 20 millones."


def test_s61_las_fuentes_se_deduplican_por_documento_y_seccion():
    repetido = Fragmento(IMPULSO.documento, IMPULSO.seccion, "Otro texto de la misma sección.")

    resultado = consultar(
        "¿Cuánto financia Impulso?",
        buscador=_con_soporte([IMPULSO, repetido, MICROSEGURO]),
        repositorio=RepositorioDoble(),
        redactor=RedactorDoble(usados=[1, 2, 3]),
    )

    assert [(f.documento, f.seccion) for f in resultado.fuentes] == [
        ("Productos de Crédito", "Crédito Productivo Impulso"),
        ("Microseguros", "Cobertura"),
    ]
    assert resultado.fuentes[0].fragmento == "Monto de 1 a 20 millones."


def test_s61_c1_solo_los_fragmentos_declarados_usados_son_fuentes():
    resultado = consultar(
        "¿Cuánto financia Impulso?",
        buscador=_con_soporte([IMPULSO, CONDICIONES, MICROSEGURO]),
        repositorio=RepositorioDoble(),
        redactor=RedactorDoble(usados=[2]),
    )

    assert [(f.documento, f.seccion, f.fragmento) for f in resultado.fuentes] == [
        ("Productos de Crédito", "Condiciones", "Plazo de hasta 36 meses.")
    ]


def test_s61_c1_las_fuentes_siguen_el_orden_de_los_fragmentos_recuperados():
    resultado = consultar(
        "¿Cuánto financia Impulso?",
        buscador=_con_soporte([IMPULSO, CONDICIONES, MICROSEGURO]),
        repositorio=RepositorioDoble(),
        redactor=RedactorDoble(usados=[3, 1]),
    )

    assert [f.seccion for f in resultado.fuentes] == ["Crédito Productivo Impulso", "Cobertura"]


# --- T8 (D10, AC-14, S-11.1, S-11.2): el caso de uso registra cada consulta con un doble ---------


class RepositorioDoble:
    """API asumida: `registrar(*, request_id, pregunta, resultado, modo)` (ver test_repositorio)."""

    def __init__(self, error: Exception | None = None) -> None:
        self.registros: list[dict[str, object]] = []
        self._error = error

    def registrar(self, *, request_id: str, pregunta: str, resultado, modo: str) -> None:
        if self._error is not None:
            raise self._error
        self.registros.append(
            {"request_id": request_id, "pregunta": pregunta, "resultado": resultado, "modo": modo}
        )


class RedactorConModo(RedactorDoble):
    modo = "extractivo"


def test_s111_consultar_registra_la_exitosa_con_el_mismo_resultado_que_devuelve():
    repo = RepositorioDoble()

    resultado = consultar(
        "¿Cuánto financia Impulso?",
        buscador=_con_soporte([IMPULSO]),
        redactor=RedactorConModo(usados=[1]),
        repositorio=repo,
    )

    assert len(repo.registros) == 1
    registro = repo.registros[0]
    assert registro["pregunta"] == "¿Cuánto financia Impulso?"
    assert registro["resultado"] == resultado
    assert registro["modo"] == "extractivo"


def test_s111_consultar_registra_sin_informacion_con_modo_ninguno():
    repo = RepositorioDoble()

    resultado = consultar(
        "¿Va a llover?",
        buscador=_sin_soporte(),
        redactor=RedactorConModo(),
        repositorio=repo,
    )

    assert len(repo.registros) == 1
    assert repo.registros[0]["resultado"] == resultado
    assert resultado.estado == Estado.SIN_INFORMACION
    assert repo.registros[0]["modo"] == "ninguno"


def test_s111_consultar_usa_el_request_id_recibido_o_genera_un_uuid_v4():
    import uuid

    repo = RepositorioDoble()
    rid = str(uuid.uuid4())
    buscador = _sin_soporte()

    consultar("p", buscador=buscador, redactor=RedactorDoble(), repositorio=repo, request_id=rid)
    consultar("p", buscador=buscador, redactor=RedactorDoble(), repositorio=repo)

    assert repo.registros[0]["request_id"] == rid
    assert uuid.UUID(str(repo.registros[1]["request_id"])).version == 4


def test_s112_si_el_repositorio_falla_consultar_propaga_el_error_sin_devolver_respuesta():
    import pytest

    repo = RepositorioDoble(error=RuntimeError("disco lleno"))

    with pytest.raises(RuntimeError, match="disco lleno"):
        consultar(
            "¿Cuánto financia Impulso?",
            buscador=_con_soporte([IMPULSO]),
            redactor=RedactorConModo(usados=[1]),
            repositorio=repo,
        )
    with pytest.raises(RuntimeError, match="disco lleno"):
        consultar(
            "¿Va a llover?", buscador=_sin_soporte(), redactor=RedactorDoble(), repositorio=repo
        )


def test_d10_consultar_exige_repositorio():
    import pytest

    with pytest.raises(TypeError):
        consultar(
            "¿Cuánto financia Impulso?", buscador=_con_soporte([IMPULSO]), redactor=RedactorDoble()
        )  # type: ignore[call-arg]
    with pytest.raises(TypeError):
        consultar("¿Va a llover?", buscador=_sin_soporte(), redactor=RedactorDoble())  # type: ignore[call-arg]
