import re
import sqlite3
import unicodedata

from py_rust_stemmers import SnowballStemmer

PALABRAS_VACIAS = frozenset(
    """a al algo ante con contra cual cuales cuando cuanta cuantas cuanto cuantos como de del desde
    donde e el ella ellas ellos en entre es esa esas ese eso esos esta estan estas este esto estos
    ha han hay la las le les lo los me mi mis muy o para pero por que quien quienes se ser si sin
    son su sus te tu tus u un una unas uno unos y yo""".split()
)


_RAIZ = SnowballStemmer("spanish")


def sin_tildes(texto: str) -> str:
    descompuesto = unicodedata.normalize("NFD", texto.casefold())
    return "".join(c for c in descompuesto if not unicodedata.combining(c))


def raices(texto: str) -> list[str]:
    """Normalización compartida (D4): la usan el texto indexado y la pregunta, así coinciden."""
    palabras = re.findall(r"[a-z0-9]+", sin_tildes(texto))
    return [_RAIZ.stem_word(p) for p in palabras if p not in PALABRAS_VACIAS]


def consulta_fts(pregunta: str) -> str | None:
    """Consulta FTS5 segura (D5): cada raíz entre comillas dobles, unidas con OR."""
    palabras = raices(pregunta)
    if not palabras:
        return None
    return " OR ".join(f'"{p.replace(chr(34), chr(34) * 2)}"' for p in dict.fromkeys(palabras))


def buscar_fts(conexion: sqlite3.Connection, pregunta: str, limite: int = 5) -> list[str]:
    """Hashes de `fragmentos` en orden BM25. Sin palabras útiles no ejecuta ningún MATCH."""
    consulta = consulta_fts(pregunta)
    if consulta is None:
        return []
    filas = conexion.execute(
        "SELECT f.hash FROM fragmentos_fts JOIN fragmentos f ON f.id = fragmentos_fts.rowid "
        "WHERE fragmentos_fts MATCH ? ORDER BY bm25(fragmentos_fts) LIMIT ?",
        (consulta, limite),
    ).fetchall()
    return [str(fila[0]) for fila in filas]
