"""T7 (MDO-0001): guardrail de salida del redactor con modelo (D7, AC-4, AC-5; S-4.2, S-5.1).

API asumida (design.md D7 describe las reglas, pero no nombra el módulo ni las firmas):

    src/server/infraestructura/redactor/validacion.py
        SalidaModelo(pydantic.BaseModel)
            respuesta: str
            fragmentos_usados: list[int]            ids 1-based en la lista numerada entregada
            partes_sin_soporte: list[str] = []
        SalidaInvalida(Exception)                   se lanza cuando la salida debe descartarse
        validar_salida(salida: SalidaModelo, fragmentos: Sequence[Fragmento]) -> RespuestaRedactada
            Devuelve la respuesta validada o lanza SalidaInvalida (el redactor Gemini la captura y
            pasa al extractivo). Por cada parte en `partes_sin_soporte` el CÓDIGO agrega al final
            "No encontré información sobre <parte>." (D7: la frase la arma el código).

Reglas que fijan estas pruebas:
    - id fuera de 1..len(fragmentos) (0, negativo, len+1) -> SalidaInvalida (S-4.2).
    - `fragmentos_usados` vacío -> SalidaInvalida, salvo que el modelo declare partes sin soporte
      (declaración "ninguna parte tiene soporte", S-5.1: se devuelve fragmentos_usados vacío).
    - toda cifra de `respuesta` debe aparecer, como cifra completa, en el texto de los fragmentos
      CITADOS (no en los no citados) (AC-4).
ASSUMPTION (no fijado en D7, ver informe): las cifras de `partes_sin_soporte` se validan igual que
las de `respuesta`, y una `respuesta` vacía o en blanco se descarta.
"""

import pytest

from src.server.dominio.modelos import Fragmento
from src.server.infraestructura.redactor.validacion import (
    SalidaInvalida,
    SalidaModelo,
    validar_salida,
)

IMPULSO = Fragmento(
    documento="Productos de Crédito.md",
    seccion="Crédito Productivo Impulso",
    texto="Monto máximo: USD 50.000. Plazo máximo: 36 meses. Descuento por pronto pago del 15%.",
)
AHORRO = Fragmento(
    documento="Productos de Ahorro.md",
    seccion="Cuenta Ahorro Plus",
    texto="Apertura con USD 100. Rendimiento mensual del 2,5%.",
)
FRAGMENTOS = [IMPULSO, AHORRO]


def _salida(respuesta: str, usados: list[int], partes: list[str] | None = None) -> SalidaModelo:
    return SalidaModelo(
        respuesta=respuesta, fragmentos_usados=usados, partes_sin_soporte=partes or []
    )


# --- salida válida -------------------------------------------------------------------------


def test_S_4_2_salida_valida_con_cifras_en_el_fragmento_citado_se_acepta():
    r = validar_salida(_salida("El monto máximo es USD 50.000 a 36 meses.", [1]), FRAGMENTOS)

    assert r.respuesta == "El monto máximo es USD 50.000 a 36 meses."
    assert list(r.fragmentos_usados) == [1]
    assert list(r.partes_sin_soporte) == []


def test_S_4_2_respuesta_sin_cifras_con_ids_validos_se_acepta():
    r = validar_salida(_salida("Está dirigido a pequeños comerciantes.", [1, 2]), FRAGMENTOS)

    assert list(r.fragmentos_usados) == [1, 2]


# --- ids no recuperados (S-4.2) ------------------------------------------------------------


@pytest.mark.parametrize("ids", [[3], [0], [-1], [1, 3], [99]])
def test_S_4_2_id_fuera_de_rango_o_no_recuperado_se_descarta(ids):
    with pytest.raises(SalidaInvalida):
        validar_salida(_salida("El monto máximo es USD 50.000.", ids), FRAGMENTOS)


# --- fragmentos_usados vacío (D7) ----------------------------------------------------------


def test_D7_fragmentos_usados_vacio_sin_partes_sin_soporte_se_descarta():
    with pytest.raises(SalidaInvalida):
        validar_salida(_salida("El monto máximo es USD 50.000.", []), FRAGMENTOS)


def test_D7_fragmentos_usados_vacio_y_respuesta_sin_datos_se_descarta_si_no_declara_partes():
    with pytest.raises(SalidaInvalida):
        validar_salida(_salida("Hay información disponible.", []), FRAGMENTOS)


# --- cifras ausentes de los fragmentos citados (AC-4, S-4.2/C1) ----------------------------


def test_AC_4_cifra_inventada_que_no_esta_en_ningun_fragmento_se_descarta():
    with pytest.raises(SalidaInvalida):
        validar_salida(_salida("El monto máximo es USD 80.000.", [1]), FRAGMENTOS)


def test_AC_4_cifra_presente_solo_en_fragmento_no_citado_se_descarta():
    # 2,5% existe en el fragmento 2, pero el modelo solo citó el 1.
    with pytest.raises(SalidaInvalida):
        validar_salida(_salida("El monto es USD 50.000 con rendimiento 2,5%.", [1]), FRAGMENTOS)


def test_AC_4_cifra_se_compara_completa_y_no_como_subcadena():
    # "5%" es subcadena de "15%" pero no es la misma cifra.
    with pytest.raises(SalidaInvalida):
        validar_salida(_salida("Tiene un descuento del 5%.", [1]), FRAGMENTOS)


def test_AC_4_cifra_con_separador_de_miles_y_simbolo_de_moneda_coincide():
    r = validar_salida(_salida("Hasta $50.000.", [1]), FRAGMENTOS)

    assert "50.000" in r.respuesta


def test_AC_4_cifra_decimal_con_coma_del_fragmento_citado_coincide():
    r = validar_salida(_salida("Rinde 2,5% al mes.", [2]), FRAGMENTOS)

    assert "2,5%" in r.respuesta


def test_AC_4_cifras_de_varios_fragmentos_citados_se_aceptan():
    r = validar_salida(_salida("USD 50.000 de monto y apertura con USD 100.", [1, 2]), FRAGMENTOS)

    assert list(r.fragmentos_usados) == [1, 2]


# --- partes sin soporte (AC-5, S-5.1) ------------------------------------------------------


def test_S_5_1_el_codigo_agrega_la_frase_no_encontre_informacion_sobre_la_parte():
    r = validar_salida(
        _salida("El monto máximo es USD 50.000.", [1], ["la tasa"]),
        FRAGMENTOS,
    )

    assert r.respuesta.startswith("El monto máximo es USD 50.000.")
    assert r.respuesta.endswith("No encontré información sobre la tasa.")
    assert list(r.partes_sin_soporte) == ["la tasa"]
    assert list(r.fragmentos_usados) == [1]


def test_S_5_1_cada_parte_sin_soporte_agrega_su_frase_en_orden():
    r = validar_salida(
        _salida("El monto máximo es USD 50.000.", [1], ["la tasa", "la comisión"]),
        FRAGMENTOS,
    )

    frase_tasa = "No encontré información sobre la tasa."
    frase_comision = "No encontré información sobre la comisión."
    assert r.respuesta.index(frase_tasa) < r.respuesta.index(frase_comision)
    assert r.respuesta.endswith(frase_comision)


def test_S_5_1_sin_partes_sin_soporte_no_se_agrega_ninguna_frase():
    r = validar_salida(_salida("El monto máximo es USD 50.000.", [1]), FRAGMENTOS)

    assert "No encontré información" not in r.respuesta


def test_S_5_1_ninguna_parte_con_soporte_se_acepta_con_fragmentos_usados_vacio():
    r = validar_salida(
        _salida("No hay datos en la base documental.", [], ["la tasa"]),
        FRAGMENTOS,
    )

    assert list(r.fragmentos_usados) == []
    assert list(r.partes_sin_soporte) == ["la tasa"]
    assert "No encontré información sobre la tasa." in r.respuesta


def test_S_5_1_C1_declaracion_sin_soporte_con_cifra_en_la_respuesta_se_descarta():
    # Sin fragmentos citados no hay dónde respaldar una cifra: no se da ni se estima una tasa.
    with pytest.raises(SalidaInvalida):
        validar_salida(_salida("La tasa estimada es 12%.", [], ["la tasa"]), FRAGMENTOS)


def test_S_5_1_C1_cifra_inventada_dentro_de_una_parte_sin_soporte_se_descarta():
    # ASSUMPTION: la frase armada por el código no puede ser vía para colar una cifra.
    with pytest.raises(SalidaInvalida):
        validar_salida(
            _salida("El monto máximo es USD 50.000.", [1], ["la tasa del 12%"]),
            FRAGMENTOS,
        )


def test_S_5_1_C1_tasa_inventada_junto_a_un_monto_valido_se_descarta():
    with pytest.raises(SalidaInvalida):
        validar_salida(
            _salida("El monto máximo es USD 50.000 y la tasa es 18%.", [1], ["la tasa"]),
            FRAGMENTOS,
        )


# --- otras reglas --------------------------------------------------------------------------


@pytest.mark.parametrize("respuesta", ["", "   ", "\n"])
def test_D7_respuesta_vacia_o_en_blanco_se_descarta(respuesta):
    # ASSUMPTION: no hay nada que entregar; se pasa al extractivo.
    with pytest.raises(SalidaInvalida):
        validar_salida(_salida(respuesta, [1]), FRAGMENTOS)


def test_D7_sin_fragmentos_recuperados_cualquier_id_es_invalido():
    with pytest.raises(SalidaInvalida):
        validar_salida(_salida("Hay información.", [1]), [])
