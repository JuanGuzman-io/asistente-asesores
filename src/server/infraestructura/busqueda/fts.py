import re
import sqlite3
import unicodedata

PALABRAS_VACIAS = frozenset(
    """a al algo ante con contra cual cuales cuando cuanta cuantas cuanto cuantos como de del desde
    donde e el ella ellas ellos en entre es esa esas ese eso esos esta estan estas este esto estos
    ha han hay la las le les lo los me mi mis muy o para pero por que quien quienes se ser si sin
    son su sus te tu tus u un una unas uno unos y yo""".split()
)


def _sin_tildes(texto: str) -> str:
    descompuesto = unicodedata.normalize("NFD", texto.casefold())
    return "".join(c for c in descompuesto if not unicodedata.combining(c))


def consulta_fts(pregunta: str) -> str | None:
    """Consulta FTS5 segura (D5): cada palabra útil entre comillas dobles, unidas con OR."""
    palabras = [
        p for p in re.findall(r"[a-z0-9]+", _sin_tildes(pregunta)) if p not in PALABRAS_VACIAS
    ]
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
