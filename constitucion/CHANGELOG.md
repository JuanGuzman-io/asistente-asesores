---
schema_version: 1
---

# Constitution changelog

<!-- Newest first. Only /mandao-close (or /mandao-constitution in active mode, with approval) writes here. -->

## 2026-10-23 — Cierre de MDO-0003: bloqueo de consultas que comprometen la seguridad

- **Cambio:** `critical-flows.md` nombra la suite e2e `tests/server/e2e/test_flujo_bloqueo.py` del flujo
  "Consulta bloqueada por seguridad" y le suma los datos de otros clientes. `business-rules.md` marca BR-4 y
  BR-8 como implementadas en `src/server/dominio/guardrail_entrada.py`. `security.md` nombra las tres
  categorías en el threat model y la limitación del guardrail por reglas. `model-registry.md` registra el
  dataset `consultas@v5` (EV-1 a EV-9). `glossary.md` agrega "Categoría de bloqueo".
- **Motivo:** Constitution Impact de `design.md` de MDO-0003; intake I-4 y Q-5.
- **Verificación:** MDO-0003 verificado (`verify-report.md`: 527 pruebas unitarias, 11 e2e y 11 evals en PASS;
  EV-8 = 1,00 y EV-9 = 0).
- **Origen:** MDO-0003, aprobado por el PE (2026-10-23).

## 2026-10-23 — Cierre de MDO-0002: interfaz para consultar

- **Cambio:** `standards.md` cierra los OPEN del frontend: lint con ESLint y typescript-eslint (complejidad,
  largo de función y de archivo), exemplar files, y los gates del proyecto `web` en `.mandao/config.yml`.
  También acepta BlueOak-1.0.0, CC-BY-4.0 (transitivas sin modificar) y OFL-1.1 (fuentes Geist), y agrega dos
  reglas de Kaizen: el `AGENTS.md` del módulo va en files y en Done when, y la primera tarea define la
  resolución y el lint de pruebas que viven fuera del paquete. `architecture.md` fija versiones del frontend
  y el proxy de Vite (D2) y quita la frase "no hay código todavía". `critical-flows.md` suma la suite
  `tests/web/e2e/consultar.spec.ts`. `security.md` prohíbe que un servidor de desarrollo sirva la raíz del
  repositorio. `ux.md` agrega la marca W+IA, la dirección visual y los tokens de la paleta de Banco W.
  `product.md` pasa el frontend a `implemented`.
- **Motivo:** Constitution Impact y Product Impact de `spec.md` de MDO-0002; Kaizen de MDO-0002 (3 de 4 FAIL
  del revisor por `AGENTS.md` o archivos no declarados; T1 F1 exponía `Data/` desde Vite); renombre a W+IA.
- **Verificación:** MDO-0002 verificado (`verify-report.md`: 67 pruebas unitarias y 4 e2e en PASS en la CI del
  PR #2, corrida 40025377094).
- **Origen:** MDO-0002, aprobado por el PE (2026-10-23).

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
