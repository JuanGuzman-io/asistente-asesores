import json
import sqlite3
from datetime import UTC, datetime

from src.server.dominio.modelos import Resultado

INSERTAR = (
    "INSERT INTO consultas(request_id, pregunta, fecha_hora, respuesta, fuentes, estado, modo)"
    " VALUES (?, ?, ?, ?, ?, ?, ?)"
)


class RepositorioConsultasSqlite:
    """Registra cada consulta (D10): un INSERT por transaccion; la pregunta nunca va a logs."""

    def __init__(self, conexion: sqlite3.Connection) -> None:
        self._conexion = conexion

    def registrar(self, *, request_id: str, pregunta: str, resultado: Resultado, modo: str) -> None:
        fuentes = json.dumps(
            [
                {"documento": f.documento, "seccion": f.seccion, "fragmento": f.fragmento}
                for f in resultado.fuentes
            ],
            ensure_ascii=False,
        )
        fila = (
            request_id,
            pregunta,
            datetime.now(UTC).isoformat(timespec="seconds"),
            resultado.respuesta,
            fuentes,
            resultado.estado.name,
            modo,
        )
        try:
            self._conexion.execute(INSERTAR, fila)
            self._conexion.commit()
        except BaseException:
            self._conexion.rollback()
            raise
