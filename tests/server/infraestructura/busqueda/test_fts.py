"""T16 (MDO-0001): S-3.3, FTS5 reduce a raíz en español el texto indexado y la pregunta (D4, C-10).

API asumida: `raices(texto) -> list[str]` en `fts.py` (minúsculas, sin tildes, solo palabras
alfanuméricas, sin palabras vacías, cada una reducida a su raíz); `consulta_fts` y el índice la usan.
Sin red: el índice se arma con el doble de embeddings de `test_indice.py` (FTS no usa vectores).
"""

import unicodedata

from src.server.infraestructura.busqueda.fts import buscar_fts, raices
from src.server.infraestructura.busqueda.indice import reconstruir_indice
from tests.server.infraestructura.busqueda.test_indice import EmbeddingsDoble

PREGUNTA_PE = "¿Cuánto le prestan como máximo a un pequeño comerciante?"
ESPERADO = ("Productos de Crédito", "Crédito Productivo Impulso")


def test_s33_singular_plural_y_sin_tilde_comparten_raiz() -> None:
    assert raices("pequeño") == raices("pequeños") == raices("pequenos")
    assert raices("comerciante") == raices("comerciantes")
    assert len(raices("pequeño")) == 1


def test_s33_la_normalizacion_quita_palabras_vacias_y_signos() -> None:
    assert raices("¿Cuánto es el monto?") == raices("monto")


def test_s33_con_fts_sobre_data_la_pregunta_del_pe_encuentra_credito_productivo_impulso(
    conexion, qdrant, oficiales
) -> None:
    reconstruir_indice(oficiales, conexion=conexion, qdrant=qdrant, embeddings=EmbeddingsDoble())

    hashes = buscar_fts(conexion, PREGUNTA_PE, 5)

    assert hashes, "FTS no encontró nada"
    documento, seccion = conexion.execute(
        "SELECT documento, seccion FROM fragmentos WHERE hash = ?", (hashes[0],)
    ).fetchone()
    assert (unicodedata.normalize("NFC", documento), seccion) == ESPERADO
