import sqlite3
import threading
from collections.abc import Sequence
from contextlib import closing

from fastapi import APIRouter, Request

from src.server.aplicacion.consultar import consultar
from src.server.config import UMBRAL_ALTO, UMBRAL_BAJO
from src.server.dominio.modelos import Fragmento
from src.server.dominio.puertos import Redactor, RespuestaRedactada
from src.server.http.esquemas import ConsultaEntrada, ConsultaSalida, FuenteSalida
from src.server.infraestructura.busqueda.buscador import BuscadorHibrido
from src.server.infraestructura.persistencia.repositorio import RepositorioConsultasSqlite

router = APIRouter()


class RedactorLimitado:
    """Limita con un semáforo las llamadas simultáneas al redactor compartido (D9).

    No guarda estado entre llamadas: el `modo` de cada una viaja en `RespuestaRedactada.modo`.
    """

    modo: str

    def __init__(self, redactor: Redactor, semaforo: threading.BoundedSemaphore) -> None:
        self._redactor = redactor
        self._semaforo = semaforo
        self.modo = redactor.modo  # solo por si la respuesta no trae `modo`

    def redactar(self, pregunta: str, fragmentos: Sequence[Fragmento]) -> RespuestaRedactada:
        with self._semaforo:
            return self._redactor.redactar(pregunta, fragmentos)


@router.post("/api/consultar")
def consultar_api(entrada: ConsultaEntrada, request: Request) -> ConsultaSalida:
    app = request.app
    # Una conexión por petición (tabla ACID): se abre y se cierra aquí, en el mismo hilo.
    with closing(sqlite3.connect(app.state.ruta_sqlite)) as conexion:
        buscador = BuscadorHibrido(
            conexion=conexion,
            qdrant=app.state.qdrant,
            embeddings=app.state.embeddings,
            umbral_alto=UMBRAL_ALTO,
            umbral_bajo=UMBRAL_BAJO,
        )
        resultado = consultar(
            entrada.pregunta,
            buscador=buscador,
            redactor=RedactorLimitado(app.state.redactor, app.state.semaforo_redactor),
            repositorio=RepositorioConsultasSqlite(conexion),
            request_id=request.state.request_id,
        )
    request.state.fuentes = len(resultado.fuentes)
    request.state.estado = resultado.estado.value
    return ConsultaSalida(
        respuesta=resultado.respuesta,
        fuentes=[
            FuenteSalida(documento=f.documento, seccion=f.seccion, fragmento=f.fragmento)
            for f in resultado.fuentes
        ],
        estado=resultado.estado.value,
    )
