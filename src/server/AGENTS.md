# Backend (`src/server/`)

Python 3.13 con `uv`. Gates: `uv run ruff format --check .`, `uv run ruff check .`, `uv run mypy src` (strict), `uv run pytest`.

- `dominio/modelos.py`: `Fragmento(documento, seccion, texto)` y `Fuente(documento, seccion, fragmento)`.
- `dominio/reglas.py`: `deduplicar_fuentes(fragmentos)` deja una fuente por `documento > sección`, en orden de primera aparición (D6).
- `config.py`: directorio `Data/` y lista de excluidos (`Información restringida.md`).
- `infraestructura/documentos/cargador.py`: `cargar_documentos(directorio, excluidos)` fragmenta por `##` (o `#` si no hay `##`). Excluye por lista y por `CONFIDENCIAL` (sin distinguir mayúsculas) en las primeras 10 líneas; el log nombra el archivo, nunca su contenido. Los nombres se normalizan a NFC. El contenido duplicado se descarta por sha256 del texto normalizado (minúsculas, espacios colapsados), por documento y por fragmento; gana el primer archivo en orden alfabético (D6). `hash_normalizado(texto)` es la única regla de hash de contenido: la usan el cargador y `busqueda/indice.py` (no reimplementarla).
- `infraestructura/busqueda/embeddings.py`: protocolo `Embeddings` (`nombre`, `embeber(textos)`) y `EmbeddingsFastembed` (modelo `MODELO_EMBEDDINGS` de `config.py`, `paraphrase-multilingual-MiniLM-L12-v2`, 384 dim; se descarga en la primera llamada, nunca en las pruebas, que usan un doble).
- `infraestructura/busqueda/esquema.py`: `crear_esquema(conexion)` crea `fragmentos` y `fragmentos_fts` (FTS5 de contenido externo, `unicode61 remove_diacritics 2`).
- `infraestructura/busqueda/indice.py`: `reconstruir_indice(fragmentos, *, conexion, qdrant, embeddings)` (D11): sube a Qdrant solo hashes nuevos (id = UUID v5 del hash), reconstruye SQLite en una transacción `BEGIN IMMEDIATE` y borra los puntos obsoletos solo tras el commit. El nombre del modelo vive en la metadata de la colección `fragmentos`; si cambia, se recrea. Registra `fragmentos=N embeddings_nuevos=K duracion_ms=T`, sin contenido. La búsqueda (T4) debe filtrar por los hashes presentes en `fragmentos`.
- `http/app.py`: `crear_app(*, directorio_datos, excluidos, directorio_qdrant, ruta_sqlite, embeddings)`. El `lifespan` abre un único `QdrantClient` y la conexión SQLite, indexa y los cierra al apagar (D13); un solo worker.
