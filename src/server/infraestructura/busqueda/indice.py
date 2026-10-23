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
VERSION_FORMATO = "v3-clave-texto-indexable"


def texto_indexable(fragmento: Fragmento) -> str:
    """Texto que se embebe y se indexa en FTS5; el hash de dedup sigue sobre `texto`."""
    return f"{fragmento.documento} > {fragmento.seccion}\n{fragmento.texto}"


def clave_embedding(fragmento: Fragmento) -> str:
    """Clave del caché de embeddings: hash de lo que se embebe, no solo del `texto`."""
    return hash_normalizado(texto_indexable(fragmento))


def _id_punto(clave: str) -> str:
    return str(uuid.uuid5(uuid.NAMESPACE_OID, clave))


def _preparar_coleccion(qdrant: QdrantClient, modelo: str) -> None:
    esperada = {"modelo": modelo, "version_formato": VERSION_FORMATO}
    if qdrant.collection_exists(COLECCION):
        metadata = qdrant.get_collection(COLECCION).config.metadata or {}
        if metadata.get("modelo") == modelo and metadata.get("version_formato") == VERSION_FORMATO:
            return
        qdrant.delete_collection(COLECCION)
    qdrant.create_collection(
        COLECCION,
        vectors_config=VectorParams(size=DIMENSION_EMBEDDINGS, distance=Distance.COSINE),
        metadata=esperada,
    )


def _claves_en_qdrant(qdrant: QdrantClient) -> set[str]:
    claves: set[str] = set()
    siguiente = None
    while True:
        puntos, siguiente = qdrant.scroll(
            COLECCION, limit=1000, offset=siguiente, with_payload=["clave"], with_vectors=False
        )
        claves.update(str(p.payload["clave"]) for p in puntos if p.payload)
        if siguiente is None:
            return claves


def _subir_nuevos(
    qdrant: QdrantClient, nuevos: list[tuple[str, str, str]], embeddings: Embeddings
) -> None:
    for inicio in range(0, len(nuevos), LOTE):
        lote = nuevos[inicio : inicio + LOTE]
        vectores = embeddings.embeber([texto for _, _, texto in lote])
        qdrant.upsert(
            COLECCION,
            points=[
                PointStruct(id=_id_punto(clave), vector=vector, payload={"hash": h, "clave": clave})
                for (clave, h, _), vector in zip(lote, vectores, strict=True)
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
            cursor = conexion.execute(
                "INSERT INTO fragmentos (documento, seccion, texto, hash) VALUES (?, ?, ?, ?)",
                (fragmento.documento, fragmento.seccion, fragmento.texto, hash_fragmento),
            )
            conexion.execute(
                "INSERT INTO fragmentos_fts(rowid, seccion, texto) VALUES (?, ?, ?)",
                (cursor.lastrowid, fragmento.seccion, texto_indexable(fragmento)),
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
    claves = {clave_embedding(f): (h, texto_indexable(f)) for f, h in con_hash}
    existentes = _claves_en_qdrant(qdrant)
    nuevos = [(c, h, t) for c, (h, t) in claves.items() if c not in existentes]

    _subir_nuevos(qdrant, nuevos, embeddings)
    _reconstruir_sqlite(conexion, con_hash)
    obsoletos = existentes - claves.keys()
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
