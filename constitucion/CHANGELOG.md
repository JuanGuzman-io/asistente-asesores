---
schema_version: 1
---

# Constitution changelog

<!-- Newest first. Only /mandao-close (or /mandao-constitution in active mode, with approval) writes here. -->

## 2026-10-23 — Qdrant local como almacén de vectores; Python 3.13 con uv

- **Cambio:** `architecture.md` reemplaza `sqlite-vec` por Qdrant en modo local (`qdrant-client` 1.20.0,
  sin servidor); SQLite queda para el registro de consultas y FTS5. Python fijado en 3.13
  (`.python-version`), instalación con `uv`; FastAPI 0.161.1. `model-registry.md` fija los embeddings
  (`paraphrase-multilingual-MiniLM-L12-v2`) y agrega la sección "Almacén de vectores".
- **Motivo:** `sqlite-vec` necesita que el Python cargue extensiones de SQLite; el Python 3.13.4 de pyenv
  falló (`AttributeError: 'sqlite3.Connection' object has no attribute 'enable_load_extension'`), y la
  solución debe poder ejecutarse completamente en local en cualquier máquina (PDF, entregable 6).
- **Verificación:** con `uv` y Python 3.13.16 y 3.13.4, `qdrant-client` 1.20.0 + `fastembed` 0.9.0 en
  `QdrantClient(path=…)`: embedding de 384 dimensiones, inserción y búsqueda correctas.
- **Alternativas descartadas:** similitud coseno en memoria (no es una base vectorial); Chroma y LanceDB
  (no ofrecen el paso directo de local a servidor con el mismo cliente).
- **Origen:** MDO-0001, decisión del PE (2026-10-23).
