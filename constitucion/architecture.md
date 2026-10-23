---
schema_version: 1
level: workspace
status: approved
last_reviewed: 2026-10-23
owner: tech lead
---

# Architecture (TRD)

Proyecto nuevo: no hay código todavía. Lo que sigue es la arquitectura elegida (decisiones del equipo,
2026-10-23); las versiones se fijan en el lockfile al crear cada proyecto.

## Stack
| Project | Language | Frameworks (versions) | Style-defining libraries |
|---|---|---|---|
| backend | Python 3.13 (fijado en `.python-version`; entorno e instalación con `uv`) | FastAPI 0.161.1 | Pydantic (validación), `sqlite3` + FTS5, `qdrant-client` 1.20.0 (modo local), `fastembed` 0.9.0, `google-genai` 2.33.0 |
| frontend | TypeScript | React + Vite | — (el diseño visual no se evalúa) |
| pruebas | Python / TypeScript | pytest + `TestClient` de FastAPI; Vitest + Testing Library | — |

## Chosen architecture
**Monolito modular en un repositorio, con arquitectura hexagonal en el backend.** El caso de uso
`consultar` depende de puertos (`BuscadorDocumental`, `RepositorioConsultas`, `Redactor`) y la
infraestructura los implementa. Así se cambia la búsqueda, la persistencia o el modelo sin tocar las
reglas, y las pruebas usan dobles deterministas.

## Layers and allowed dependencies
`http` (rutas FastAPI, validación de entrada) → `aplicacion` (caso de uso `consultar`) → `dominio`
(guardrails, estados, reglas de respuesta, puertos) ← `infraestructura` (cargador de documentos, índice,
SQLite, embeddings, Gemini). `dominio` no importa nada de las demás capas; `web` solo habla con la API.

## Module boundaries
| Module | Responsibility | Public contract |
|---|---|---|
| `src/server/http` | Exponer `POST /api/consultar` y `GET /api/consultas`; validar entrada | Contrato del PDF: `{ pregunta }` → `{ respuesta, fuentes }` (+ `estado`) |
| `src/server/aplicacion` | Orquestar: guardrail de entrada → búsqueda → redacción → guardrail de salida → registro | `consultar(pregunta) -> Resultado` |
| `src/server/dominio` | Guardrails, estados, mensaje sin información, umbral de relevancia | Tipos `Estado`, `Resultado`, `Fuente`; puertos |
| `src/server/infraestructura/documentos` | Cargar `Data/`, excluir confidenciales, deduplicar, fragmentar por sección `##` | Fragmentos con `documento > sección` |
| `src/server/infraestructura/busqueda` | Búsqueda híbrida: FTS5 (palabras, BM25) en SQLite + Qdrant local (vectores coseno de embeddings locales con `fastembed`) | Implementa `BuscadorDocumental` |
| `src/server/infraestructura/persistencia` | Guardar cada consulta en SQLite | Implementa `RepositorioConsultas` |
| `src/server/infraestructura/redactor` | Redactar con Gemini (`google-genai`) a partir de los fragmentos; sin clave, respuesta extractiva | Implementa `Redactor` |
| `src/web` | Consultar y mostrar respuesta, fuentes, errores y estado de procesamiento | Consume la API |

## Patterns and conventions
- **Dos almacenes locales, sin servidores:** un archivo SQLite guarda las consultas y el índice FTS5;
  Qdrant en modo local (`QdrantClient(path=…)`, carpeta fuera de git) guarda los vectores de los
  fragmentos con distancia coseno. No se usan extensiones de SQLite, así que cualquier Python 3.13 sirve.
  Al pasar a producción, el mismo código apunta a un servidor Qdrant cambiando la configuración.
- **Recuperación híbrida:** se combinan los puntajes de FTS5 y de Qdrant. Si el mejor fragmento no
  supera el umbral, el estado es `Sin información suficiente` y no se llama al modelo.
- **Redacción:** con `GEMINI_API_KEY`, Gemini redacta solo con los fragmentos recuperados y debe citarlos.
  Sin clave, o si la API falla, la respuesta es extractiva (fragmento y fuente). Ver `model-registry.md`.
- Los embeddings son locales: se calculan una vez al indexar y solo se recalculan si cambia un documento.
- Los guardrails son código y corren antes de buscar y antes de responder.

## Integrations
Gemini API (Google), opcional por configuración. Qdrant corre embebido en el proceso (modo local), no
como servicio externo.

## Quality attributes
- Ejecutable 100 % local; sin clave de API sigue funcionando en modo extractivo (PDF, entregables 5-6).
- Sin información suficiente → mensaje fijo, nunca una respuesta inventada.
- Ver presupuestos en `performance.md`.
