---
schema_version: 1
spec: MDO-0001-consultar-la-base-documental-con-fuentes
status: draft
---

# Data model — Consultar la base documental con fuentes

Proyecto nuevo: no existe esquema. Se crea un único archivo SQLite con el registro de consultas, los
fragmentos de la base documental, su índice de palabras (FTS5) y una caché de embeddings en BLOB, que se
cargan en memoria para la similitud coseno ([C-3](requirements.md#c-3)) y evitan recalcular lo que no
cambió.

## Changes

### ADDED — Consulta (`consultas`)

| Field | Type | Constraints | Classification |
|---|---|---|---|
| `id` | INTEGER | PK autoincremental | interna |
| `request_id` | TEXT | NOT NULL, UNIQUE; UUID v4 | interna |
| `pregunta` | TEXT | NOT NULL; NFC, 1–1.000 puntos de código tras quitar espacios exteriores ([FR-7](requirements.md#fr7)) | `pii` (puede traer datos de clientes) |
| `fecha_hora` | TEXT | NOT NULL; UTC ISO 8601 | interna |
| `respuesta` | TEXT | NOT NULL | interna |
| `fuentes` | TEXT | NOT NULL; JSON `[{documento, seccion, fragmento}]`, `[]` sin fuentes | interna |
| `estado` | TEXT | NOT NULL; CHECK en `EXITOSA`, `SIN_INFORMACION`, `BLOQUEADA` | interna |
| `modo` | TEXT | NOT NULL; CHECK en `modelo`, `extractivo`, `ninguno` | interna |

`modo` lo exige la observabilidad (DP-7, NFR-4): distingue respuestas del modelo, del respaldo
extractivo ([FR-12](requirements.md#fr12)) y las que no redactan (sin información).

### ADDED — Fragmento (`fragmentos`)

| Field | Type | Constraints | Classification |
|---|---|---|---|
| `id` | INTEGER | PK | interna |
| `documento` | TEXT | NOT NULL; nombre del archivo sin `.md` | interna |
| `seccion` | TEXT | NOT NULL; título `##` (o el `#` si el documento no tiene `##`) | interna |
| `texto` | TEXT | NOT NULL | interna |
| `hash` | TEXT | NOT NULL, UNIQUE; sha256 del texto normalizado ([FR-2](requirements.md#fr2)) | interna |

Nunca contiene filas de documentos confidenciales ([FR-1](requirements.md#fr1)).

### ADDED — Índice de palabras (`fragmentos_fts`)

Tabla virtual FTS5 de contenido externo sobre `fragmentos(seccion, texto)`, `content_rowid=id`,
tokenizador `unicode61 remove_diacritics 2` ([FR-8](requirements.md#fr8) S-8.2).

### ADDED — Caché de embeddings (`embeddings_cache`)

| Field | Type | Constraints | Classification |
|---|---|---|---|
| `hash` | TEXT | PK; mismo hash que `fragmentos.hash` | interna |
| `modelo` | TEXT | NOT NULL; nombre del modelo de embeddings | interna |
| `embedding` | BLOB | NOT NULL; 384 float32 (1.536 bytes), `paraphrase-multilingual-MiniLM-L12-v2` ([design.md#d4](design.md#d4)) | interna |

Sobrevive a la reconstrucción del índice ([NFR-2](requirements.md#nfr-2--arranque)); una fila con otro
`modelo` se ignora. Al arrancar, los embeddings de los fragmentos vigentes se cargan en una matriz en
memoria para la similitud coseno.

### MODIFIED — ninguno

### REMOVED — ninguno

## Relationships and indexes

- `fragmentos.id` ↔ `fragmentos_fts.rowid` (1:1).
- `fragmentos.hash` ↔ `embeddings_cache.hash` (0..1).
- `consultas` no referencia a `fragmentos`: guarda las fuentes como copia, porque el índice se reconstruye
  en cada arranque y el registro debe conservar lo que se respondió.
- Índice sobre `consultas(fecha_hora)` para el historial de MDO-0003.

## Permissions

Archivo local de un solo usuario; sin roles (`security.md`: sin autenticación en la prueba). El archivo
queda fuera de git (`.gitignore`).

## State transitions

`consultas.estado` se fija una vez al insertar; no hay transiciones. `BLOQUEADA` queda permitido por el
CHECK pero solo lo escribe MDO-0002.

## Migration

- **Expand:** creación del esquema al arrancar (`CREATE TABLE IF NOT EXISTS`), versión en `PRAGMA user_version = 1`.
- **Backfill:** no aplica; no hay datos.
- **Contract:** no aplica.
- **Rollback:** borrar el archivo SQLite; el índice se reconstruye desde `Data/` y las consultas
  registradas se pierden (aceptable en la prueba local).

## Evidence

- Sin esquema previo: Premise Ledger [P1](design.md#p1).
