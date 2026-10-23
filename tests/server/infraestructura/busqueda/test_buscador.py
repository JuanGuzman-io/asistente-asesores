"""T4 (MDO-0001): búsqueda híbrida FTS5 + Qdrant, RRF, umbral 0,60 / 0,54 (D4, D5).

API asumida (design.md fija el puerto `BuscadorDocumental`, los umbrales y la fusión, pero no firmas):

    src/server/config.py
        UMBRAL_ALTO = 0.60, UMBRAL_BAJO = 0.54 ("valores calibrados en configuración", D4).

    src/server/dominio/puertos.py
        ResultadoBusqueda (dataclass congelada): `fragmentos: Sequence[Fragmento]` (hasta 3, mejor
        primero; vacío si no hay soporte) y `hay_soporte: bool`.
        BuscadorDocumental (Protocol): `buscar(pregunta: str) -> ResultadoBusqueda`.

    src/server/infraestructura/busqueda/fts.py
        consulta_fts(pregunta: str) -> str | None: D5. Normaliza (casefold, sin tildes), conserva solo
            palabras alfanuméricas, quita palabras vacías del español, cada palabra entre comillas
            dobles y unidas con " OR ". `None` si no queda ninguna palabra útil (se omite la vía FTS).
        buscar_fts(conexion, pregunta, limite=5) -> list[str]: hashes de `fragmentos` en orden BM25;
            lista vacía si `consulta_fts` es `None` (sin ejecutar ningún MATCH). Usa `MATCH ?`.

    src/server/infraestructura/busqueda/buscador.py
        BuscadorHibrido(*, conexion, qdrant, embeddings, umbral_alto=UMBRAL_ALTO,
                        umbral_bajo=UMBRAL_BAJO) -> implementa BuscadorDocumental.
            5 candidatos por vía, RRF (k = 60), se quedan los 3 primeros, solo hashes presentes en
            `fragmentos` (D11). Hay soporte si el mejor fragmento (el primero tras la fusión) tiene
            coseno >= umbral_alto, o >= umbral_bajo y además salió en FTS.

Cambio del PE (2026-10-23): lo que se embebe y se indexa en FTS es `texto_indexable(fragmento)` =
`f"{documento} > {seccion}\n{texto}"` (`src/server/infraestructura/busqueda/indice.py`). Los dobles
de vectores explícitos se indexan por ese texto (`_emb`), escrito aquí en literal a propósito.

Doble de embeddings temático: el texto de un fragmento (sin su título) o la pregunta que hablan del
mismo producto comparten eje (coseno 1); lo demás cae en un vector hash casi ortogonal. Los casos de
umbral usan vectores con coseno exacto. Sin red ni descarga de modelos.
"""

import hashlib
import math
import re
import sqlite3
import unicodedata
import uuid
from collections.abc import Sequence

import pytest

from src.server import config
from src.server.dominio.modelos import Fragmento
from src.server.dominio.puertos import BuscadorDocumental, ResultadoBusqueda
from src.server.infraestructura.busqueda.buscador import BuscadorHibrido
from src.server.infraestructura.busqueda.fts import buscar_fts, consulta_fts
from src.server.infraestructura.busqueda.indice import reconstruir_indice
from src.server.infraestructura.documentos.cargador import hash_normalizado

DIMENSION = 384
COLECCION = "fragmentos"
IMPULSO = ("Productos de Crédito", "Crédito Productivo Impulso")
PREGUNTA_S31 = "¿Cuál es el monto máximo del Crédito Productivo Impulso?"
PREGUNTA_S81 = (
    '¿Cuál es el monto máximo del "Crédito" Productivo Impulso? (urgente) \U0001f60a * - :'
)
PREGUNTA_S82 = "cual es el monto maximo del credito productivo impulso"
SIN_SOPORTE = [
    "¿Cuál es la tasa de interés de un crédito?",
    "¿Cuánto cuesta la prima mensual de un microseguro?",
    "¿Cuántos meses tarda el tiempo de respuesta de una queja?",
    "¿Cuál es el horario de la oficina principal?",
]
HOSTILES = [
    '"',
    '""',
    '"Crédito',
    "(",
    ")",
    "*",
    "-",
    ":",
    "^",
    "+",
    "OR",
    "AND",
    "NOT",
    "NEAR(",
    "NEAR(monto máximo, 2)",
    "seccion:impulso",
    "{seccion texto}: impulso",
    "monto* -máximo",
    "'; DROP TABLE fragmentos; --",
    "monto OR OR máximo",
    "\U0001f60a\U0001f4b8",
    "¿¡?!",
    "ñandú señor año ¿Cuánto?",
]
SOLO_SIGNOS = ["\U0001f60a", "* - :", '" " "', "¿?¡!", "\U0001f60a * - :"]

# Temas del doble temático: palabras del cuerpo del fragmento o de la pregunta -> eje.
TEMAS = {
    0: {"impulso", "comerciantes", "microempresarios", "productivo"},
    1: {"agro", "siembra", "maquinaria", "riego", "rural"},
    2: {"mujer", "emprende", "mentoria", "ferias", "formacion"},
}


def _palabras(texto: str) -> list[str]:
    plano = "".join(
        c for c in unicodedata.normalize("NFD", texto.casefold()) if not unicodedata.combining(c)
    )
    return re.findall(r"[a-z0-9]+", plano)


def _hash_vector(clave: str, nombre: str) -> list[float]:
    crudo = hashlib.shake_256(f"{nombre}\0{clave}".encode()).digest(DIMENSION)
    return [(b - 127.5) / 127.5 for b in crudo]


class EmbeddingsTematico:
    nombre = "doble-tematico"

    def embeber(self, textos: Sequence[str]) -> list[list[float]]:
        return [self._vector(t) for t in textos]

    def _vector(self, texto: str) -> list[float]:
        palabras = set(_palabras(texto))
        for eje, claves in TEMAS.items():
            if palabras & claves:
                vector = [0.0] * DIMENSION
                vector[eje] = 1.0
                return vector
        return _hash_vector(texto, self.nombre)


class EmbeddingsFijo:
    """Vectores explícitos por texto; lo desconocido cae en un vector hash casi ortogonal."""

    nombre = "doble-fijo"

    def __init__(self, vectores: dict[str, list[float]]) -> None:
        self.vectores = vectores

    def embeber(self, textos: Sequence[str]) -> list[list[float]]:
        return [self.vectores.get(t) or _hash_vector(t, self.nombre) for t in textos]


def _emb(fragmento: Fragmento) -> str:
    """Texto que llega al modelo de embeddings: `documento > sección\ntexto`."""
    return f"{fragmento.documento} > {fragmento.seccion}\n{fragmento.texto}"


def _con_coseno(c: float) -> list[float]:
    """Vector cuyo coseno con la consulta `_consulta()` es exactamente `c`."""
    vector = [0.0] * DIMENSION
    vector[0], vector[1] = c, math.sqrt(1 - c * c)
    return vector


def _consulta() -> list[float]:
    vector = [0.0] * DIMENSION
    vector[0] = 1.0
    return vector


def _indexar(conexion, qdrant, fragmentos, embeddings) -> BuscadorHibrido:
    reconstruir_indice(fragmentos, conexion=conexion, qdrant=qdrant, embeddings=embeddings)
    return BuscadorHibrido(conexion=conexion, qdrant=qdrant, embeddings=embeddings)


def _clave(resultado: ResultadoBusqueda) -> list[tuple[str, str]]:
    return [(unicodedata.normalize("NFC", f.documento), f.seccion) for f in resultado.fragmentos]


@pytest.fixture
def buscador(conexion, qdrant, oficiales) -> BuscadorHibrido:
    return _indexar(conexion, qdrant, oficiales, EmbeddingsTematico())


def _caso_umbral(conexion, qdrant, coseno: float, pregunta: str) -> ResultadoBusqueda:
    """Un fragmento "alfa beta" con el coseno dado respecto de la consulta; FTS depende de la pregunta."""
    fragmento = Fragmento("Doc", "Sección Uno", "alfa beta")
    embeddings = EmbeddingsFijo({_emb(fragmento): _con_coseno(coseno), pregunta: _consulta()})
    return _indexar(conexion, qdrant, [fragmento], embeddings).buscar(pregunta)


# --- Puerto y configuración (D4) ---------------------------------------------------------------


def test_d4_umbrales_calibrados_en_configuracion():
    assert config.UMBRAL_ALTO == pytest.approx(0.60)
    assert config.UMBRAL_BAJO == pytest.approx(0.54)


def test_d4_el_buscador_implementa_el_puerto_y_devuelve_resultado_de_dominio(buscador):
    puerto: BuscadorDocumental = buscador
    resultado = puerto.buscar(PREGUNTA_S31)
    assert isinstance(resultado, ResultadoBusqueda)
    assert isinstance(resultado.hay_soporte, bool)


# --- S-3.1 / AC-3: el primer fragmento es la sección correcta -----------------------------------


def test_s31_el_primer_fragmento_es_credito_productivo_impulso(buscador):
    resultado = buscador.buscar(PREGUNTA_S31)

    assert resultado.hay_soporte is True
    assert _clave(resultado)[0] == IMPULSO
    assert "$50.000.000" in resultado.fragmentos[0].texto  # el monto máximo que dice el documento


def test_s31_devuelve_como_maximo_tres_fragmentos_sin_repetir(buscador):
    claves = _clave(buscador.buscar(PREGUNTA_S31))

    assert 1 <= len(claves) <= 3
    assert len(set(claves)) == len(claves)


def test_s31_el_confidencial_nunca_aparece_en_los_resultados(buscador):
    for pregunta in (PREGUNTA_S31, "información restringida confidencial INT-8457"):
        for fragmento in buscador.buscar(pregunta).fragmentos:
            assert "restringida" not in fragmento.documento.casefold()


def test_s31_rrf_conserva_el_orden_y_limita_a_tres_candidatos(conexion, qdrant):
    # Misma longitud; "comun" aparece 5, 4, 3, 2 y 1 veces: BM25 ordena igual que los vectores.
    fragmentos = [
        Fragmento("Doc", f"Sección {i}", " ".join(["comun"] * (5 - i) + [f"relleno{i}"] * i))
        for i in range(5)
    ]
    cosenos = [0.9, 0.8, 0.7, 0.6, 0.5]
    vectores = {_emb(f): _con_coseno(c) for f, c in zip(fragmentos, cosenos, strict=True)}
    vectores["comun"] = _consulta()
    buscador = _indexar(conexion, qdrant, fragmentos, EmbeddingsFijo(vectores))

    resultado = buscador.buscar("comun")

    assert [f.seccion for f in resultado.fragmentos] == ["Sección 0", "Sección 1", "Sección 2"]


def test_s31_rrf_fusiona_ordenes_distintos_de_bm25_y_coseno(conexion, qdrant):
    # BM25 (más "comun" = mejor): S0, S1, S2, S3, S4. Coseno: S2 .9, S3 .8, S1 .7, S4 .65, S0 .62.
    # Rangos (FTS, coseno) y puntaje RRF = 1/(60+rf) + 1/(60+rc):
    #   S0 (1,5) = 1/61 + 1/65 = 0,031778    S1 (2,3) = 1/62 + 1/63 = 0,032002
    #   S2 (3,1) = 1/63 + 1/61 = 0,032266    S3 (4,2) = 1/64 + 1/62 = 0,031754
    #   S4 (5,4) = 1/65 + 1/64 = 0,031010
    # Fusión: S2, S1, S0. Solo BM25 daría S0, S1, S2; solo coseno, S2, S3, S1.
    fragmentos = [
        Fragmento("Doc", f"Sección {i}", " ".join(["comun"] * (5 - i) + [f"relleno{i}"] * i))
        for i in range(5)
    ]
    cosenos = [0.62, 0.7, 0.9, 0.8, 0.65]
    vectores = {_emb(f): _con_coseno(c) for f, c in zip(fragmentos, cosenos, strict=True)}
    vectores["comun"] = _consulta()
    buscador = _indexar(conexion, qdrant, fragmentos, EmbeddingsFijo(vectores))
    por_texto = dict(conexion.execute("SELECT hash, seccion FROM fragmentos").fetchall())
    assert [por_texto[h] for h in buscar_fts(conexion, "comun")] == [
        f"Sección {i}" for i in range(5)
    ]

    resultado = buscador.buscar("comun")

    assert resultado.hay_soporte is True
    assert [f.seccion for f in resultado.fragmentos] == ["Sección 2", "Sección 1", "Sección 0"]


def test_d4_sin_candidatos_comunes_usa_el_coseno_real_del_mejor_fragmento(conexion, qdrant):
    # FTS solo encuentra A ("alfa"); los 5 de Qdrant son B1..B5 (coseno .95 a .70), sin "alfa".
    # A queda fuera de los 5 de Qdrant (coseno .65) y empata en RRF con B1 (1/61 cada uno); el
    # desempate favorece a FTS. El mejor fragmento es A, y su coseno real (.65) supera el alto.
    pregunta = "alfa"
    a = Fragmento("Doc", "Sección A", "alfa gamma")
    otros = [Fragmento("Doc", f"Sección B{i}", f"bravo{i}") for i in range(1, 6)]
    vectores = {_emb(a): _con_coseno(0.65), pregunta: _consulta()}
    for f, c in zip(otros, [0.95, 0.9, 0.85, 0.8, 0.7], strict=True):
        vectores[_emb(f)] = _con_coseno(c)
    buscador = _indexar(conexion, qdrant, [a, *otros], EmbeddingsFijo(vectores))

    resultado = buscador.buscar(pregunta)

    assert resultado.hay_soporte is True
    assert resultado.fragmentos


def test_d11_los_huerfanos_no_quitan_cupos_a_los_candidatos_vigentes(conexion, qdrant):
    from qdrant_client.models import PointStruct

    pregunta = "omega"  # no está en ningún fragmento: solo cuenta la vía vectorial
    vigente = Fragmento("Doc", "Sección Vigente", "alfa beta")
    embeddings = EmbeddingsFijo({_emb(vigente): _con_coseno(0.7), pregunta: _consulta()})
    buscador = _indexar(conexion, qdrant, [vigente], embeddings)
    huerfanos = [hash_normalizado(f"huerfano {i}") for i in range(6)]  # más cercanos que el vigente
    qdrant.upsert(
        COLECCION,
        points=[
            PointStruct(
                id=str(uuid.uuid5(uuid.NAMESPACE_OID, h)),
                vector=_consulta(),
                payload={"hash": h},
            )
            for h in huerfanos
        ],
    )

    resultado = buscador.buscar(pregunta)

    assert resultado.hay_soporte is True
    assert [f.seccion for f in resultado.fragmentos] == ["Sección Vigente"]


# --- Umbral D4: 0,60 solo vectores; 0,54 si además coincide en FTS ------------------------------


def test_s31_umbral_alto_basta_sin_coincidencia_fts(conexion, qdrant):
    resultado = _caso_umbral(conexion, qdrant, 0.65, "omega")  # "omega" no está en el fragmento

    assert resultado.hay_soporte is True
    assert [f.seccion for f in resultado.fragmentos] == ["Sección Uno"]


def test_s31_umbral_bajo_con_coincidencia_fts_da_soporte(conexion, qdrant):
    assert _caso_umbral(conexion, qdrant, 0.56, "alfa").hay_soporte is True


def test_s32_entre_umbrales_sin_coincidencia_fts_no_hay_soporte(conexion, qdrant):
    resultado = _caso_umbral(conexion, qdrant, 0.56, "omega")

    assert resultado.hay_soporte is False
    assert not resultado.fragmentos


def test_s32_bajo_el_umbral_bajo_no_hay_soporte_aunque_coincida_en_fts(conexion, qdrant):
    resultado = _caso_umbral(conexion, qdrant, 0.35, "alfa")

    assert resultado.hay_soporte is False
    assert not resultado.fragmentos


def test_s31_la_busqueda_ignora_puntos_cuyo_hash_no_esta_en_fragmentos(conexion, qdrant):
    from qdrant_client.models import PointStruct

    pregunta = "omega"
    fragmento = Fragmento("Doc", "Sección Uno", "alfa beta")
    embeddings = EmbeddingsFijo({_emb(fragmento): _con_coseno(0.2), pregunta: _consulta()})
    buscador = _indexar(conexion, qdrant, [fragmento], embeddings)
    huerfano = hash_normalizado("huerfano gamma")
    qdrant.upsert(  # idéntico a la consulta (coseno 1), pero sin fila en `fragmentos`
        COLECCION,
        points=[
            PointStruct(
                id=str(uuid.uuid5(uuid.NAMESPACE_OID, huerfano)),
                vector=_consulta(),
                payload={"hash": huerfano},
            )
        ],
    )

    resultado = buscador.buscar(pregunta)

    assert resultado.hay_soporte is False
    assert not resultado.fragmentos


# --- S-3.2 / AC-11: sin soporte -----------------------------------------------------------------


@pytest.mark.parametrize("pregunta", SIN_SOPORTE)
def test_s32_pregunta_sin_respuesta_en_la_base_no_supera_el_umbral(buscador, pregunta):
    resultado = buscador.buscar(pregunta)

    assert resultado.hay_soporte is False
    assert not resultado.fragmentos


# --- S-8.1 / AC-8: tildes, signos y emojis ------------------------------------------------------


def test_s81_pregunta_con_signos_da_el_mismo_resultado_que_sin_ellos(buscador):
    limpia = buscador.buscar(PREGUNTA_S31)
    con_signos = buscador.buscar(PREGUNTA_S81)

    assert con_signos.hay_soporte is True
    assert _clave(con_signos) == _clave(limpia)
    assert _clave(con_signos)[0] == IMPULSO


def test_s81_consulta_fts_cita_cada_palabra_y_quita_palabras_vacias():
    consulta = consulta_fts(PREGUNTA_S81)

    assert consulta is not None
    assert re.fullmatch(r'"[^"]+"( OR "[^"]+")*', consulta)
    terminos = {t.strip('"') for t in consulta.split(" OR ")}
    plano = {
        "".join(c for c in unicodedata.normalize("NFD", t) if not unicodedata.combining(c))
        for t in terminos
    }
    assert {"monto", "maximo", "credito", "productivo", "impulso", "urgente"} <= plano
    assert not plano & {"cual", "es", "el", "del", "de", "un"}
    assert not any(c in consulta.replace('"', "") for c in "*:()-¿?\U0001f60a")


@pytest.mark.parametrize("pregunta", SOLO_SIGNOS)
def test_s81_solo_signos_o_emojis_omiten_la_via_fts(conexion, qdrant, oficiales, pregunta):
    buscador = _indexar(conexion, qdrant, oficiales, EmbeddingsTematico())
    sentencias: list[str] = []
    conexion.set_trace_callback(sentencias.append)

    assert consulta_fts(pregunta) is None
    assert buscar_fts(conexion, pregunta) == []
    resultado = buscador.buscar(pregunta)

    assert isinstance(resultado, ResultadoBusqueda)
    assert not any("MATCH" in s.upper() for s in sentencias)


def test_s81_c1_ninguna_pregunta_hostil_produce_error_de_sintaxis_fts(buscador, conexion):
    for pregunta in HOSTILES:
        try:
            resultado = buscador.buscar(pregunta)
            hashes = buscar_fts(conexion, pregunta)
        except sqlite3.OperationalError as error:  # p. ej. "fts5: syntax error near ..."
            pytest.fail(f"{pregunta!r} produjo un error de sintaxis de búsqueda: {error}")
        assert isinstance(resultado, ResultadoBusqueda), pregunta
        assert isinstance(hashes, list), pregunta


def test_s81_c1_los_operadores_fts_se_tratan_como_palabras_no_como_sintaxis(buscador, conexion):
    # "NOT impulso" como operador excluiría Impulso; como palabras, lo encuentra.
    hashes = buscar_fts(conexion, "Crédito NOT Impulso OR AND NEAR")

    impulso = conexion.execute(
        "SELECT hash FROM fragmentos WHERE seccion = ?", (IMPULSO[1],)
    ).fetchone()[0]
    assert impulso in hashes


def test_s81_c1_la_pregunta_nunca_se_interpola_en_el_sql(conexion, qdrant, oficiales):
    buscador = _indexar(conexion, qdrant, oficiales, EmbeddingsTematico())
    antes = conexion.execute("SELECT count(*) FROM fragmentos").fetchone()[0]
    sentencias: list[str] = []
    conexion.set_trace_callback(sentencias.append)

    buscador.buscar("x'; DROP TABLE fragmentos; --")

    assert conexion.execute("SELECT count(*) FROM fragmentos").fetchone()[0] == antes > 0
    assert not any("DROP TABLE" in s.upper() and "MATCH" not in s.upper() for s in sentencias)


# --- S-8.2: sin tildes ---------------------------------------------------------------------------


def test_s82_sin_tildes_recupera_el_mismo_fragmento_que_con_tildes(buscador):
    con_tildes = buscador.buscar(PREGUNTA_S31)
    sin_tildes = buscador.buscar(PREGUNTA_S82)

    assert sin_tildes.hay_soporte is True
    assert _clave(sin_tildes)[0] == IMPULSO
    assert _clave(sin_tildes) == _clave(con_tildes)


def test_s82_la_via_fts_por_si_sola_ignora_tildes_y_ordena_primero_la_seccion(
    conexion, qdrant, oficiales
):
    _indexar(conexion, qdrant, oficiales, EmbeddingsTematico())
    impulso = conexion.execute(
        "SELECT hash FROM fragmentos WHERE seccion = ?", (IMPULSO[1],)
    ).fetchone()[0]

    con_tildes = buscar_fts(conexion, PREGUNTA_S31)
    sin_tildes = buscar_fts(conexion, PREGUNTA_S82)

    assert con_tildes[0] == impulso
    assert sin_tildes == con_tildes
    assert len(sin_tildes) <= 5


def test_fts_encuentra_por_palabras_del_documento_y_de_la_seccion(conexion, qdrant):
    # El texto indexado en FTS es `documento > sección\ntexto`: el cuerpo no trae esas palabras.
    fragmento = Fragmento("Manual Zorrodoc", "Sección Zorrosec", "alfa beta")
    otro = Fragmento("Otro", "Otra", "gamma delta")
    _indexar(conexion, qdrant, [fragmento, otro], EmbeddingsTematico())

    assert buscar_fts(conexion, "zorrodoc") == [hash_normalizado(fragmento.texto)]
    assert buscar_fts(conexion, "zorrosec") == [hash_normalizado(fragmento.texto)]
