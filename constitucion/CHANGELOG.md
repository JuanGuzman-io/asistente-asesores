---
schema_version: 1
---

# Constitution changelog

<!-- Newest first. Only /mandao-close (or /mandao-constitution in active mode, with approval) writes here. -->

## 2026-10-23 — Cierre de MDO-0001: backend de consulta con fuentes

- **Cambio:** `architecture.md` fija un solo proceso de uvicorn y el semáforo de llamadas a Gemini.
  `critical-flows.md` nombra la suite e2e del flujo "Consulta respondida con fuentes y registrada".
  `standards.md` fija mypy en modo estricto, nombra los exemplar files del backend, registra la excepción
  de licencias para dependencias transitivas, apunta los gates del backend a `.mandao/config.yml` y agrega
  dos reglas de Kaizen: verificar con una llamada real las premisas sobre APIs externas y fijar el texto
  exacto de los mensajes de error en la spec. `glossary.md` agrega "Modo de respuesta". `product.md` pasa
  a `implemented` responder con fuentes, indicar falta de información y registrar consultas. Los dueños
  (PO y tech lead) pasan a PE en toda la constitución.
- **Motivo:** Constitution Impact y Product Impact de `design.md` de MDO-0001; Kaizen de MDO-0001
  (CC-1, CC-5); decisiones del PE sobre licencias y dueños.
- **Verificación:** MDO-0001 verificado (`verify-report.md`: 273 pruebas unitarias, 17 e2e y evals
  `consultas@v3` en PASS).
- **Origen:** MDO-0001, aprobado por el PE (2026-10-23).

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
