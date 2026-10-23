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


class RedactorExclusivo:
    """Aísla el `modo` de cada petición sobre un redactor compartido.

    `RedactorGemini.modo` es estado de instancia: se escribe en `redactar`. El candado cubre la
    llamada y la lectura del `modo`, que se copia a esta instancia, propia de la petición.
    """

    def __init__(self, redactor: Redactor, candado: threading.Lock) -> None:
        self._redactor = redactor
        self._candado = candado
        self.modo = redactor.modo

    def redactar(self, pregunta: str, fragmentos: Sequence[Fragmento]) -> RespuestaRedactada:
        with self._candado:
            respuesta = self._redactor.redactar(pregunta, fragmentos)
            self.modo = self._redactor.modo
        return respuesta


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
            redactor=RedactorExclusivo(app.state.redactor, app.state.candado_redactor),
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
