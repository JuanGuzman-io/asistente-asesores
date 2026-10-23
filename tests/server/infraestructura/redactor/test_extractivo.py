"""T6 (MDO-0001): sin modelo, la respuesta es extractiva y no afirma cubrir toda la pregunta (D12, C-1).

API asumida (design.md D12 describe el comportamiento, pero no nombra el módulo ni la clase):

    src/server/infraestructura/redactor/extractivo.py
        RedactorExtractivo()  sin argumentos; implementa el Protocol `Redactor`:
            redactar(pregunta, fragmentos) -> RespuestaRedactada
        - respuesta = "Esto es lo que encontré en la base documental:" seguida, por cada uno de los
          primeros 2 fragmentos, de "Documento > Sección" y el texto del fragmento.
        - fragmentos_usados = ids 1-based de los fragmentos incluidos ([1] o [1, 2]).
        - partes_sin_soporte = () siempre (el extractivo no nombra partes faltantes).
        El umbral ya lo aplicó el buscador: el redactor recibe solo fragmentos con soporte.
"""

from collections.abc import Sequence

from src.server.aplicacion.consultar import consultar
from src.server.dominio.estados import Estado
from src.server.dominio.modelos import Fragmento
from src.server.dominio.puertos import ResultadoBusqueda
from src.server.infraestructura.redactor.extractivo import RedactorExtractivo

FRASE = "Esto es lo que encontré en la base documental:"

IMPULSO = Fragmento(
    documento="Productos de Crédito.md",
    seccion="Crédito Productivo Impulso",
    texto=(
        "Dirigido a pequeños comerciantes y microempresarios.\n\n"
        "| Concepto | Valor |\n|---|---|\n"
        "| Monto mínimo | $2.000.000 |\n| Monto máximo | $50.000.000 |\n"
        "| Plazo máximo | 60 meses |"
    ),
)
AGRO = Fragmento(
    documento="Productos de Crédito.md",
    seccion="Crédito Agro Crece",
    texto="| Monto máximo | $80.000.000 |\n| Plazo máximo | 84 meses |",
)
REQUISITOS = Fragmento(
    documento="Requisitos.md",
    seccion="Documentos",
    texto="Documento de identidad y evidencia de ingresos.",
)

PREGUNTA_MONTO = "¿Cuál es el monto máximo del Crédito Productivo Impulso?"
PREGUNTA_MONTO_TASA = "¿Cuál es el monto máximo y la tasa del Crédito Productivo Impulso?"


class RepositorioDoble:
    def registrar(self, *, request_id: str, pregunta: str, resultado: object, modo: str) -> None:
        pass


class _Buscador:
    def __init__(self, fragmentos: Sequence[Fragmento]) -> None:
        self._fragmentos = fragmentos

    def buscar(self, pregunta: str) -> ResultadoBusqueda:
        return ResultadoBusqueda(fragmentos=self._fragmentos, hay_soporte=True)


def test_s_4_1_la_respuesta_extractiva_contiene_el_monto_maximo_del_documento() -> None:
    redactada = RedactorExtractivo().redactar(PREGUNTA_MONTO, [IMPULSO])

    assert "$50.000.000" in redactada.respuesta


def test_s_4_1_c1_declara_usado_al_menos_un_fragmento_y_consultar_trae_fuente_exitosa() -> None:
    resultado = consultar(
        PREGUNTA_MONTO,
        buscador=_Buscador([IMPULSO]),
        repositorio=RepositorioDoble(),
        redactor=RedactorExtractivo(),
    )

    assert resultado.estado is Estado.EXITOSA
    assert "$50.000.000" in resultado.respuesta
    assert len(resultado.fuentes) >= 1
    assert (resultado.fuentes[0].documento, resultado.fuentes[0].seccion) == (
        "Productos de Crédito.md",
        "Crédito Productivo Impulso",
    )


def test_s_5_2_la_respuesta_empieza_con_la_frase_fija() -> None:
    redactada = RedactorExtractivo().redactar(PREGUNTA_MONTO_TASA, [IMPULSO])

    assert redactada.respuesta.startswith(FRASE)


def test_s_5_2_trae_el_fragmento_del_credito_productivo_impulso_con_su_fuente() -> None:
    resultado = consultar(
        PREGUNTA_MONTO_TASA,
        buscador=_Buscador([IMPULSO]),
        repositorio=RepositorioDoble(),
        redactor=RedactorExtractivo(),
    )

    assert resultado.estado is Estado.EXITOSA
    assert IMPULSO.texto in resultado.respuesta
    assert [(f.documento, f.seccion) for f in resultado.fuentes] == [
        ("Productos de Crédito.md", "Crédito Productivo Impulso")
    ]


def test_s_5_2_c1_no_afirma_responder_toda_la_pregunta_ni_da_una_tasa() -> None:
    redactada = RedactorExtractivo().redactar(PREGUNTA_MONTO_TASA, [IMPULSO])
    minusculas = redactada.respuesta.lower()

    assert "tasa" not in minusculas
    assert "%" not in redactada.respuesta
    for afirmacion in ("responde toda", "respuesta completa", "toda la pregunta", "no encontré"):
        assert afirmacion not in minusculas
    assert redactada.partes_sin_soporte == ()


def test_cada_fragmento_va_precedido_por_documento_mayor_que_seccion() -> None:
    respuesta = RedactorExtractivo().redactar(PREGUNTA_MONTO, [IMPULSO, AGRO]).respuesta

    encabezado_1 = "Productos de Crédito.md > Crédito Productivo Impulso"
    encabezado_2 = "Productos de Crédito.md > Crédito Agro Crece"
    assert respuesta.index(encabezado_1) < respuesta.index(IMPULSO.texto)
    assert respuesta.index(encabezado_2) < respuesta.index(AGRO.texto)
    assert respuesta.index(IMPULSO.texto) < respuesta.index(encabezado_2)


def test_usa_como_maximo_dos_fragmentos_de_los_tres_recibidos() -> None:
    redactada = RedactorExtractivo().redactar(PREGUNTA_MONTO, [IMPULSO, AGRO, REQUISITOS])

    assert list(redactada.fragmentos_usados) == [1, 2]
    assert REQUISITOS.texto not in redactada.respuesta
    assert "Requisitos.md > Documentos" not in redactada.respuesta


def test_con_un_solo_fragmento_declara_solo_el_id_uno() -> None:
    redactada = RedactorExtractivo().redactar(PREGUNTA_MONTO, [IMPULSO])

    assert list(redactada.fragmentos_usados) == [1]
