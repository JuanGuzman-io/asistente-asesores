import sqlite3

SENTENCIAS = (
    """CREATE TABLE IF NOT EXISTS fragmentos (
        id INTEGER PRIMARY KEY,
        documento TEXT NOT NULL,
        seccion TEXT NOT NULL,
        texto TEXT NOT NULL,
        hash TEXT NOT NULL UNIQUE
    )""",
    """CREATE VIRTUAL TABLE IF NOT EXISTS fragmentos_fts USING fts5(
        seccion, texto,
        content='fragmentos', content_rowid='id',
        tokenize='unicode61 remove_diacritics 2'
    )""",
)


def crear_esquema(conexion: sqlite3.Connection) -> None:
    for sentencia in SENTENCIAS:
        conexion.execute(sentencia)
    conexion.commit()
