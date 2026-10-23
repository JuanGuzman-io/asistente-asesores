import logging
import sqlite3
import time
import uuid
from collections.abc import Sequence

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    PointIdsList,
    PointStruct,
    VectorParams,
)

from src.server.dominio.modelos import Fragmento
from src.server.infraestructura.busqueda.embeddings import DIMENSION_EMBEDDINGS, Embeddings
from src.server.infraestructura.busqueda.esquema import crear_esquema
from src.server.infraestructura.documentos.cargador import hash_normalizado

registro = logging.getLogger(__name__)

COLECCION = "fragmentos"
LOTE = 64


def _id_punto(hash_fragmento: str) -> str:
    return str(uuid.uuid5(uuid.NAMESPACE_OID, hash_fragmento))


def _preparar_coleccion(qdrant: QdrantClient, modelo: str) -> None:
    if qdrant.collection_exists(COLECCION):
        metadata = qdrant.get_collection(COLECCION).config.metadata or {}
        if metadata.get("modelo") == modelo:
            return
        qdrant.delete_collection(COLECCION)
    qdrant.create_collection(
        COLECCION,
        vectors_config=VectorParams(size=DIMENSION_EMBEDDINGS, distance=Distance.COSINE),
        metadata={"modelo": modelo},
    )


def _hashes_en_qdrant(qdrant: QdrantClient) -> set[str]:
    hashes: set[str] = set()
    siguiente = None
    while True:
        puntos, siguiente = qdrant.scroll(
            COLECCION, limit=1000, offset=siguiente, with_payload=["hash"], with_vectors=False
        )
        hashes.update(str(p.payload["hash"]) for p in puntos if p.payload)
        if siguiente is None:
            return hashes


def _subir_nuevos(
    qdrant: QdrantClient, nuevos: list[tuple[str, str]], embeddings: Embeddings
) -> None:
    for inicio in range(0, len(nuevos), LOTE):
        lote = nuevos[inicio : inicio + LOTE]
        vectores = embeddings.embeber([texto for _, texto in lote])
        qdrant.upsert(
            COLECCION,
            points=[
                PointStruct(id=_id_punto(h), vector=vector, payload={"hash": h})
                for (h, _), vector in zip(lote, vectores, strict=True)
            ],
        )


def _reconstruir_sqlite(
    conexion: sqlite3.Connection, fragmentos: Sequence[tuple[Fragmento, str]]
) -> None:
    conexion.execute("BEGIN IMMEDIATE")
    try:
        conexion.execute("DELETE FROM fragmentos")
        conexion.execute("INSERT INTO fragmentos_fts(fragmentos_fts) VALUES ('delete-all')")
        for fragmento, hash_fragmento in fragmentos:
            conexion.execute(
                "INSERT INTO fragmentos (documento, seccion, texto, hash) VALUES (?, ?, ?, ?)",
                (fragmento.documento, fragmento.seccion, fragmento.texto, hash_fragmento),
            )
        conexion.execute(
            "INSERT INTO fragmentos_fts(rowid, seccion, texto) "
            "SELECT id, seccion, texto FROM fragmentos"
        )
    except BaseException:
        conexion.rollback()
        raise
    conexion.commit()


def reconstruir_indice(
    fragmentos: Sequence[Fragmento],
    *,
    conexion: sqlite3.Connection,
    qdrant: QdrantClient,
    embeddings: Embeddings,
) -> None:
    inicio = time.perf_counter()
    crear_esquema(conexion)
    _preparar_coleccion(qdrant, embeddings.nombre)
    con_hash = [(f, hash_normalizado(f.texto)) for f in fragmentos]
    vigentes = {h for _, h in con_hash}
    existentes = _hashes_en_qdrant(qdrant)
    nuevos = list({h: f.texto for f, h in con_hash if h not in existentes}.items())

    _subir_nuevos(qdrant, nuevos, embeddings)
    _reconstruir_sqlite(conexion, con_hash)
    obsoletos = existentes - vigentes
    if obsoletos:
        qdrant.delete(
            COLECCION, points_selector=PointIdsList(points=[_id_punto(h) for h in obsoletos])
        )
    registro.info(
        "Índice listo: fragmentos=%d embeddings_nuevos=%d duracion_ms=%.1f",
        len(vigentes),
        len(nuevos),
        (time.perf_counter() - inicio) * 1000,
    )
