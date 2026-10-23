import sqlite3

VERSION_ESQUEMA = 1

SENTENCIAS = (
    """CREATE TABLE IF NOT EXISTS consultas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        request_id TEXT NOT NULL UNIQUE,
        pregunta TEXT NOT NULL,
        fecha_hora TEXT NOT NULL,
        respuesta TEXT NOT NULL,
        fuentes TEXT NOT NULL,
        estado TEXT NOT NULL CHECK (estado IN ('EXITOSA', 'SIN_INFORMACION', 'BLOQUEADA')),
        modo TEXT NOT NULL CHECK (modo IN ('modelo', 'extractivo', 'ninguno'))
    )""",
    "CREATE INDEX IF NOT EXISTS idx_consultas_fecha_hora ON consultas(fecha_hora)",
)


def crear_esquema(conexion: sqlite3.Connection) -> None:
    for sentencia in SENTENCIAS:
        conexion.execute(sentencia)
    conexion.execute(f"PRAGMA user_version = {VERSION_ESQUEMA}")
    conexion.commit()
