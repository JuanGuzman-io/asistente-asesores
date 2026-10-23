"""T2 (MDO-0001): las fuentes se deduplican por `documento > sección` (D6).

API asumida (src/server/dominio/reglas.py; design.md no fija el nombre):

    deduplicar_fuentes(fragmentos: Sequence[Fragmento]) -> list[Fuente]

    Fuente: objeto con atributos `documento`, `seccion` y `fragmento` (texto del primer fragmento
    que aparece para esa clave). Conserva el orden de primera aparición.
"""

from src.server.dominio.modelos import Fragmento
from src.server.dominio.reglas import deduplicar_fuentes


def test_s22_dos_fragmentos_con_el_mismo_documento_y_seccion_dan_una_sola_fuente():
    fragmentos = [
        Fragmento("Productos de Crédito", "Condiciones", "Texto uno."),
        Fragmento("Productos de Crédito", "Condiciones", "Texto dos."),
    ]

    fuentes = deduplicar_fuentes(fragmentos)

    assert [(f.documento, f.seccion) for f in fuentes] == [("Productos de Crédito", "Condiciones")]
    assert fuentes[0].fragmento == "Texto uno."


def test_s22_conserva_el_orden_de_primera_aparicion():
    fragmentos = [
        Fragmento("B", "Dos", "b2"),
        Fragmento("A", "Uno", "a1"),
        Fragmento("B", "Dos", "b2 otra vez"),
        Fragmento("B", "Tres", "b3"),
        Fragmento("A", "Uno", "a1 otra vez"),
    ]

    fuentes = deduplicar_fuentes(fragmentos)

    assert [(f.documento, f.seccion) for f in fuentes] == [
        ("B", "Dos"),
        ("A", "Uno"),
        ("B", "Tres"),
    ]


def test_s22_misma_seccion_en_documentos_distintos_son_fuentes_distintas():
    fragmentos = [Fragmento("A", "Condiciones", "a"), Fragmento("B", "Condiciones", "b")]

    fuentes = deduplicar_fuentes(fragmentos)

    assert [(f.documento, f.seccion) for f in fuentes] == [
        ("A", "Condiciones"),
        ("B", "Condiciones"),
    ]
