"""T3 (MDO-0001): índice SQLite FTS5 + Qdrant local reconstruido al arrancar (D11, D13).

API asumida (design.md no fija nombres; se eligen los más simples coherentes con data-model.md):

    src/server/infraestructura/busqueda/embeddings.py
        Embeddings (Protocol): `nombre: str` (modelo, p. ej.
        "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2") y
        `embeber(textos: Sequence[str]) -> list[list[float]]` (vectores de 384 dimensiones).

    src/server/infraestructura/busqueda/indice.py
        reconstruir_indice(fragmentos, *, conexion, qdrant, embeddings) -> None
            fragmentos: Sequence[Fragmento]; conexion: sqlite3.Connection;
            qdrant: QdrantClient; embeddings: Embeddings.
            Crea el esquema si falta (`fragmentos`, `fragmentos_fts`, colección Qdrant
            "fragmentos"), embebe solo los hashes que la colección no tiene, reconstruye SQLite en
            una transacción y, solo tras el commit, borra de Qdrant los puntos obsoletos.
            Si algo falla, lanza la excepción (el servidor no arranca) y deja `fragmentos` intacto.

Esquema (data-model.md): `fragmentos(id, documento, seccion, texto, hash)`; `fragmentos_fts` FTS5 de
contenido externo con `rowid = fragmentos.id`; colección Qdrant "fragmentos", payload `hash` =
sha256 del texto normalizado (minúsculas, espacios colapsados).

Cambio del PE (2026-10-23), API asumida para el implementador:
    - `texto_indexable(fragmento: Fragmento) -> str` en `indice.py` (o donde sea más coherente con
      `src/server/AGENTS.md`); devuelve `f"{documento} > {seccion}\n{texto}"`. Es lo que se embebe
      y lo que indexa FTS5. El hash de dedup (`hash_normalizado`) sigue sobre `texto`.
    - `VERSION_FORMATO` en `indice.py`: constante guardada en la metadata de la colección Qdrant
      junto al nombre del modelo; si cambia, la colección se recrea. Estas pruebas escriben el
      formato en literal (`_embebido`) y solo usan `VERSION_FORMATO` vía `monkeypatch`.

La función de búsqueda es de T4: "puntos huérfanos" se demuestra con el filtro de D11 (hashes
presentes en `fragmentos`) aplicado directamente a Qdrant.

Sin red ni descarga de modelos: el doble de embeddings es determinista y cuenta sus llamadas.
"""

import hashlib
import math
import sqlite3
import unicodedata
from collections.abc import Sequence
from pathlib import Path

import pytest

from src.server.dominio.modelos import Fragmento
from src.server.infraestructura.busqueda.fts import raices
from src.server.infraestructura.busqueda.indice import reconstruir_indice

DATA = Path(__file__).resolve().parents[4] / "Data"
RESTRINGIDO = "Información restringida.md"
COLECCION = "fragmentos"
DIMENSION = 384
MODELO_A = "modelo-a"
MODELO_B = "modelo-b"
OFICIALES = {
    "Manual del Asesor Comercial",
    "Políticas de Atención",
    "Portafolio de Microseguros",
    "Procedimientos Operativos",
    "Productos de Crédito",
}


class EmbeddingsDoble:
    """Determinista (SHAKE-256 del modelo y del texto); cuenta llamadas y textos calculados."""

    def __init__(self, nombre: str = MODELO_A) -> None:
        self.nombre = nombre
        self.llamadas = 0
        self.textos: list[str] = []

    def vector(self, texto: str) -> list[float]:
        crudo = hashlib.shake_256(f"{self.nombre}\0{texto}".encode()).digest(DIMENSION)
        return [(b - 127.5) / 127.5 for b in crudo]

    def embeber(self, textos: Sequence[str]) -> list[list[float]]:
        self.llamadas += 1
        self.textos.extend(textos)
        return [self.vector(t) for t in textos]


def _hash(texto: str) -> str:
    return hashlib.sha256(" ".join(texto.casefold().split()).encode("utf-8")).hexdigest()


def _embebido(fragmento: Fragmento) -> str:
    """Texto que debe llegar al modelo de embeddings: `documento > sección\ntexto`."""
    return f"{fragmento.documento} > {fragmento.seccion}\n{fragmento.texto}"


def _coseno(a: Sequence[float], b: Sequence[float]) -> float:
    producto = sum(x * y for x, y in zip(a, b, strict=True))
    return producto / (math.sqrt(sum(x * x for x in a)) * math.sqrt(sum(y * y for y in b)))


def _frag(documento: str, seccion: str, texto: str) -> Fragmento:
    return Fragmento(documento, seccion, texto)


def _puntos(qdrant) -> list:
    puntos, _ = qdrant.scroll(COLECCION, limit=1000, with_payload=True, with_vectors=True)
    return puntos


def _hashes_qdrant(qdrant) -> set[str]:
    return {p.payload["hash"] for p in _puntos(qdrant)}


def _hashes_sqlite(conexion: sqlite3.Connection) -> set[str]:
    return {fila[0] for fila in conexion.execute("SELECT hash FROM fragmentos")}


def _fts(conexion: sqlite3.Connection, palabra: str) -> int:
    # FTS indexa raíces (T16, D4): la palabra se reduce igual que en el índice.
    frase = " ".join(raices(palabra))
    if not frase:
        return 0
    consulta = '"' + frase + '"'
    return conexion.execute(
        "SELECT count(*) FROM fragmentos_fts WHERE fragmentos_fts MATCH ?", (consulta,)
    ).fetchone()[0]


def _poner_veneno(conexion: sqlite3.Connection) -> None:
    """Hace fallar en SQLite el INSERT de un fragmento con VENENO, tras el upsert en Qdrant."""
    conexion.execute(
        "CREATE TRIGGER falla_prueba BEFORE INSERT ON fragmentos "
        "WHEN NEW.texto LIKE '%VENENO%' "
        "BEGIN SELECT RAISE(ABORT, 'fallo simulado de SQLite'); END"
    )
    conexion.commit()


# --- S-1.1: los cinco oficiales quedan indexados con documento y sección --------------------


def test_s11_indexa_los_fragmentos_oficiales_en_sqlite_y_qdrant(conexion, qdrant, oficiales):
    reconstruir_indice(oficiales, conexion=conexion, qdrant=qdrant, embeddings=EmbeddingsDoble())

    filas = conexion.execute("SELECT documento, seccion, texto, hash FROM fragmentos").fetchall()
    assert len(filas) == len(oficiales) > 0
    assert {unicodedata.normalize("NFC", f[0]) for f in filas} == OFICIALES
    assert all(documento and seccion and texto for documento, seccion, texto, _ in filas)
    assert _hashes_qdrant(qdrant) == {f[3] for f in filas}
    assert all(len(p.vector) == DIMENSION for p in _puntos(qdrant))
    assert _fts(conexion, "Impulso") >= 1  # la vía FTS no es vacía


# --- S-1.1/C1: nada del confidencial en FTS5, payload ni vectores ---------------------------


def test_s11_c1_ningun_termino_ni_punto_del_confidencial_en_el_indice(conexion, qdrant, oficiales):
    restringido = (DATA / RESTRINGIDO).read_text(encoding="utf-8")
    assert "INT-8457" in restringido  # guarda: la prueba no es vacua
    oficial = " ".join(f.texto + " " + f.seccion for f in oficiales).casefold()
    # Con stemming (T16) un término distinto puede compartir raíz con uno oficial: no es una fuga.
    raices_oficiales = set(
        raices(" ".join(f.documento + " " + f.seccion + " " + f.texto for f in oficiales))
    )
    signos = ".,;:()\"'"
    unicos = {
        p.strip(signos)
        for p in restringido.split()
        if len(p.strip(signos)) >= 6
        and p.strip(signos).casefold() not in oficial
        and not set(raices(p.strip(signos))) <= raices_oficiales
    }
    assert "INT-8457-SECRET-782" in unicos
    doble = EmbeddingsDoble()

    reconstruir_indice(oficiales, conexion=conexion, qdrant=qdrant, embeddings=doble)

    # Se comparan índices, no términos, para no imprimir contenido confidencial en un fallo.
    en_fts = [n for n, t in enumerate(sorted(unicos)) if _fts(conexion, t) > 0]
    assert en_fts == []
    assert _fts(conexion, "INT-8457") == 0
    volcado = "\n".join(repr(p.payload) for p in _puntos(qdrant)).casefold()
    en_payload = [n for n, t in enumerate(sorted(unicos)) if t.casefold() in volcado]
    assert en_payload == []
    assert len(_puntos(qdrant)) == len(oficiales)  # ni un vector de más
    # El texto del confidencial ni siquiera llegó al modelo de embeddings.
    assert [n for n, t in enumerate(doble.textos) if "INT-8457" in t] == []
    documentos = [f[0] for f in conexion.execute("SELECT documento FROM fragmentos")]
    assert [d for d in documentos if d.startswith("Información restringida")] == []


# --- NFR-2 / D11: embeddings solo para hashes nuevos ----------------------------------------


def test_segundo_arranque_sin_cambios_calcula_cero_embeddings(tmp_path, oficiales):
    from qdrant_client import QdrantClient

    primero = EmbeddingsDoble()
    con = sqlite3.connect(tmp_path / "indice.db")
    q = QdrantClient(path=str(tmp_path / "qdrant"))
    reconstruir_indice(oficiales, conexion=con, qdrant=q, embeddings=primero)
    con.close()
    q.close()
    assert len(primero.textos) == len(oficiales)

    segundo = EmbeddingsDoble()
    con = sqlite3.connect(tmp_path / "indice.db")
    q = QdrantClient(path=str(tmp_path / "qdrant"))  # reinicio: Qdrant persiste en disco
    try:
        reconstruir_indice(oficiales, conexion=con, qdrant=q, embeddings=segundo)
        assert segundo.textos == []
        assert len(_hashes_sqlite(con)) == len(oficiales)
        assert len(_puntos(q)) == len(oficiales)
    finally:
        con.close()
        q.close()


def test_solo_se_calculan_los_embeddings_de_los_hashes_nuevos(conexion, qdrant):
    a = _frag("Doc", "Uno", "contenido alfa original")
    b = _frag("Doc", "Dos", "contenido beta original")
    c = _frag("Doc", "Tres", "contenido gamma nuevo")
    reconstruir_indice([a, b], conexion=conexion, qdrant=qdrant, embeddings=EmbeddingsDoble())

    doble = EmbeddingsDoble()
    reconstruir_indice([a, c], conexion=conexion, qdrant=qdrant, embeddings=doble)

    assert doble.textos == [_embebido(c)]
    assert _hashes_sqlite(conexion) == {_hash(a.texto), _hash(c.texto)}
    assert _hashes_qdrant(qdrant) == {_hash(a.texto), _hash(c.texto)}  # b obsoleto, ya borrado


# --- D11: cambiar el modelo recrea la colección ---------------------------------------------


def test_cambiar_el_nombre_del_modelo_recrea_la_coleccion(conexion, qdrant, oficiales):
    reconstruir_indice(
        oficiales, conexion=conexion, qdrant=qdrant, embeddings=EmbeddingsDoble(MODELO_A)
    )

    nuevo = EmbeddingsDoble(MODELO_B)
    reconstruir_indice(oficiales, conexion=conexion, qdrant=qdrant, embeddings=nuevo)

    assert len(nuevo.textos) == len(oficiales)  # se recalcularon todos
    puntos = _puntos(qdrant)
    assert len(puntos) == len(oficiales)
    por_hash = {_hash(f.texto): f for f in oficiales}
    for p in puntos:
        esperado = nuevo.vector(_embebido(por_hash[p.payload["hash"]]))
        assert _coseno(p.vector, esperado) > 0.999  # vectores del modelo B, no restos del A
    assert len(_hashes_sqlite(conexion)) == len(oficiales)


def test_el_texto_embebido_incluye_documento_y_seccion(conexion, qdrant):
    fragmentos = [
        _frag("Manual Uno", "Sección A", "contenido alfa"),
        _frag("Manual Dos", "Sección B", "contenido beta\ncon dos líneas"),
    ]
    doble = EmbeddingsDoble()

    reconstruir_indice(fragmentos, conexion=conexion, qdrant=qdrant, embeddings=doble)

    assert sorted(doble.textos) == sorted(
        [
            "Manual Uno > Sección A\ncontenido alfa",
            "Manual Dos > Sección B\ncontenido beta\ncon dos líneas",
        ]
    )
    # El hash de dedup sigue sobre `texto`, no sobre el texto embebido.
    assert _hashes_qdrant(qdrant) == {_hash(f.texto) for f in fragmentos}


@pytest.mark.parametrize(
    ("antes", "despues"),
    [
        (("Manual", "Sección vieja"), ("Manual", "Sección nueva")),
        (("Manual viejo", "Sección"), ("Manual nuevo", "Sección")),
    ],
    ids=["renombrar-seccion", "renombrar-documento"],
)
def test_renombrar_la_seccion_con_el_mismo_texto_vuelve_a_embeber(conexion, qdrant, antes, despues):
    # F1: la clave del caché de Qdrant es el hash de lo que se embebe (`texto_indexable`), no del
    # `texto`: si cambia solo el título, el vector del título viejo no puede quedar guardado.
    texto = "contenido que no cambia entre arranques"
    viejo = _frag(*antes, texto)
    nuevo = _frag(*despues, texto)
    reconstruir_indice([viejo], conexion=conexion, qdrant=qdrant, embeddings=EmbeddingsDoble())

    doble = EmbeddingsDoble()
    reconstruir_indice([nuevo], conexion=conexion, qdrant=qdrant, embeddings=doble)

    assert doble.textos == [_embebido(nuevo)]  # se volvió a embeber con el título nuevo
    puntos = _puntos(qdrant)
    assert len(puntos) == 1  # el punto del título viejo no sobrevive
    esperado = doble.vector(_embebido(nuevo))
    obsoleto = doble.vector(_embebido(viejo))
    assert _coseno(puntos[0].vector, esperado) > 0.999
    assert _coseno(puntos[0].vector, obsoleto) < 0.999
    fila = conexion.execute("SELECT documento, seccion, texto FROM fragmentos").fetchall()
    assert fila == [(nuevo.documento, nuevo.seccion, texto)]


def test_cambiar_la_version_del_formato_recrea_la_coleccion(
    conexion, qdrant, oficiales, monkeypatch
):
    from src.server.infraestructura.busqueda import indice

    monkeypatch.setattr(indice, "VERSION_FORMATO", "formato-a")
    reconstruir_indice(oficiales, conexion=conexion, qdrant=qdrant, embeddings=EmbeddingsDoble())

    monkeypatch.setattr(indice, "VERSION_FORMATO", "formato-b")
    nuevo = EmbeddingsDoble()  # mismo modelo: solo cambia el formato
    reconstruir_indice(oficiales, conexion=conexion, qdrant=qdrant, embeddings=nuevo)

    assert len(nuevo.textos) == len(oficiales)  # se recalcularon todos
    assert len(_puntos(qdrant)) == len(oficiales)
    assert len(_hashes_sqlite(conexion)) == len(oficiales)

    # Con la misma versión ya no se recalcula nada.
    igual = EmbeddingsDoble()
    reconstruir_indice(oficiales, conexion=conexion, qdrant=qdrant, embeddings=igual)
    assert igual.textos == []


# --- D11 fallo parcial: SQLite falla después del upsert en Qdrant ---------------------------


def _preparar_fallo(conexion, qdrant):
    a = _frag("Doc", "Uno", "zorroalfa conserva su lugar")
    b = _frag("Doc", "Dos", "zorrobeta es obsoleto pero previo")
    veneno = _frag("Doc", "Tres", "zorrogamma VENENO hace fallar SQLite")
    reconstruir_indice([a, b], conexion=conexion, qdrant=qdrant, embeddings=EmbeddingsDoble())
    _poner_veneno(conexion)
    doble = EmbeddingsDoble()
    with pytest.raises(Exception):  # noqa: B017 - el tipo lo decide el implementador
        reconstruir_indice([a, veneno], conexion=conexion, qdrant=qdrant, embeddings=doble)
    return a, b, veneno, doble


def test_falla_sqlite_tras_upsert_qdrant_conserva_indice_anterior(conexion, qdrant):
    a, b, veneno, doble = _preparar_fallo(conexion, qdrant)

    assert _embebido(veneno) in doble.textos  # el embedding se calculó antes del fallo
    # `fragmentos` y FTS conservan el índice anterior intacto.
    assert _hashes_sqlite(conexion) == {_hash(a.texto), _hash(b.texto)}
    assert _fts(conexion, "zorrobeta") == 1
    assert _fts(conexion, "zorroalfa") == 1
    assert _fts(conexion, "zorrogamma") == 0
    # Los obsoletos se borran solo tras el commit: b sigue en Qdrant; el nuevo quedó como huérfano
    # (prueba que el upsert ocurrió antes del fallo de SQLite).
    assert _hashes_qdrant(qdrant) == {_hash(a.texto), _hash(b.texto), _hash(veneno.texto)}


def test_puntos_huerfanos_no_aparecen_en_busqueda(conexion, qdrant):
    from qdrant_client.models import FieldCondition, Filter, MatchAny

    a, b, veneno, _ = _preparar_fallo(conexion, qdrant)
    huerfano = _hash(veneno.texto)
    assert huerfano in _hashes_qdrant(qdrant)  # existe en Qdrant, pero no en `fragmentos`

    # Filtro de D11: solo hashes presentes en `fragmentos`; la búsqueda con el vector exacto del
    # huérfano no lo devuelve.
    vigentes = sorted(_hashes_sqlite(conexion))
    resultado = qdrant.query_points(
        COLECCION,
        query=EmbeddingsDoble().vector(_embebido(veneno)),
        query_filter=Filter(must=[FieldCondition(key="hash", match=MatchAny(any=vigentes))]),
        limit=10,
        with_payload=True,
    ).points
    assert huerfano not in {p.payload["hash"] for p in resultado}
    assert {p.payload["hash"] for p in resultado} == set(vigentes)

    # Al siguiente arranque exitoso se borran huérfanos y obsoletos.
    d = _frag("Doc", "Cuatro", "zorrodelta es nuevo")
    reconstruir_indice([a, d], conexion=conexion, qdrant=qdrant, embeddings=EmbeddingsDoble())
    assert _hashes_qdrant(qdrant) == {_hash(a.texto), _hash(d.texto)}
    assert _hashes_sqlite(conexion) == {_hash(a.texto), _hash(d.texto)}
