import re
import sqlite3

from qdrant_client import QdrantClient
from qdrant_client.models import FieldCondition, Filter, MatchAny, MatchValue

from src.server.config import UMBRAL_ALTO, UMBRAL_BAJO
from src.server.dominio.modelos import Fragmento
from src.server.dominio.puertos import ResultadoBusqueda
from src.server.infraestructura.busqueda.embeddings import Embeddings
from src.server.infraestructura.busqueda.fts import buscar_fts, raices, sin_tildes
from src.server.infraestructura.busqueda.indice import COLECCION

CANDIDATOS = 5
RESULTADOS = 3
K_RRF = 60
# Pedido de sección: "¿Qué dice la política de…?", "¿Qué dice el manual sobre…?".
PEDIDO_DE_SECCION = re.compile(r"^\W*que\s+dicen?\b")


class BuscadorHibrido:
    """FTS5 + Qdrant fusionados con RRF (D4). Solo devuelve hashes presentes en `fragmentos`."""

    def __init__(
        self,
        *,
        conexion: sqlite3.Connection,
        qdrant: QdrantClient,
        embeddings: Embeddings,
        umbral_alto: float = UMBRAL_ALTO,
        umbral_bajo: float = UMBRAL_BAJO,
    ) -> None:
        self._conexion = conexion
        self._qdrant = qdrant
        self._embeddings = embeddings
        self._umbral_alto = umbral_alto
        self._umbral_bajo = umbral_bajo

    def buscar(self, pregunta: str) -> ResultadoBusqueda:
        por_fts = buscar_fts(self._conexion, pregunta, CANDIDATOS)
        cosenos = self._buscar_vectores(pregunta)
        puntaje: dict[str, float] = {}
        for ranking in (por_fts, list(cosenos)):
            for rango, hash_fragmento in enumerate(ranking, start=1):
                puntaje[hash_fragmento] = puntaje.get(hash_fragmento, 0.0) + 1 / (K_RRF + rango)
        orden = sorted(puntaje, key=lambda h: puntaje[h], reverse=True)[:RESULTADOS]
        if not orden:
            return ResultadoBusqueda(fragmentos=[], hay_soporte=False)

        nombrada = self._seccion_nombrada(pregunta, por_fts)
        if nombrada is not None:
            orden = [nombrada, *(h for h in orden if h != nombrada)][:RESULTADOS]
            return ResultadoBusqueda(
                fragmentos=[self._fragmento(h) for h in orden], hay_soporte=True
            )

        mejor = orden[0]
        coseno = cosenos[mejor] if mejor in cosenos else self._coseno_de(pregunta, mejor)
        hay_soporte = coseno >= self._umbral_alto or (
            coseno >= self._umbral_bajo and mejor in por_fts
        )
        if not hay_soporte:
            return ResultadoBusqueda(fragmentos=[], hay_soporte=False)
        return ResultadoBusqueda(fragmentos=[self._fragmento(h) for h in orden], hay_soporte=True)

    def _seccion_nombrada(self, pregunta: str, por_fts: list[str]) -> str | None:
        """Candidato FTS cuya sección nombra completa un pedido de sección; tiene soporte aunque
        el prefijo "¿Qué dice…?" baje su coseno. Sin pedido, decide el umbral (p. ej. "¿Cuál es la
        tasa del Crédito Productivo Impulso?" nombra la sección, pero el dato no está)."""
        if not PEDIDO_DE_SECCION.match(sin_tildes(pregunta)):
            return None
        palabras = raices(pregunta)
        for hash_fragmento in por_fts:
            (seccion,) = self._conexion.execute(
                "SELECT seccion FROM fragmentos WHERE hash = ?", (hash_fragmento,)
            ).fetchone()
            titulo = raices(seccion)
            if titulo and any(
                palabras[i : i + len(titulo)] == titulo for i in range(len(palabras))
            ):
                return hash_fragmento
        return None

    def _buscar_vectores(self, pregunta: str) -> dict[str, float]:
        """Hash -> coseno, en orden de similitud, solo de hashes vigentes en `fragmentos`."""
        vigentes = [fila[0] for fila in self._conexion.execute("SELECT hash FROM fragmentos")]
        vector = self._embeddings.embeber([pregunta])[0]
        puntos = self._qdrant.query_points(
            COLECCION,
            query=vector,
            query_filter=Filter(must=[FieldCondition(key="hash", match=MatchAny(any=vigentes))]),
            limit=CANDIDATOS,
            with_payload=["hash"],
        ).points
        return {str(p.payload["hash"]): p.score for p in puntos if p.payload}

    def _coseno_de(self, pregunta: str, hash_fragmento: str) -> float:
        """Coseno real de un fragmento que quedó fuera de los candidatos de Qdrant."""
        vector = self._embeddings.embeber([pregunta])[0]
        puntos = self._qdrant.query_points(
            COLECCION,
            query=vector,
            query_filter=Filter(
                must=[FieldCondition(key="hash", match=MatchValue(value=hash_fragmento))]
            ),
            limit=1,
        ).points
        return puntos[0].score if puntos else 0.0

    def _fragmento(self, hash_fragmento: str) -> Fragmento:
        documento, seccion, texto = self._conexion.execute(
            "SELECT documento, seccion, texto FROM fragmentos WHERE hash = ?", (hash_fragmento,)
        ).fetchone()
        return Fragmento(documento, seccion, texto)
