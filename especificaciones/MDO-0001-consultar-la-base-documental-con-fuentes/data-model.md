---
schema_version: 1
spec: MDO-0001-consultar-la-base-documental-con-fuentes
status: draft
---

# Data model — Consultar la base documental con fuentes

Proyecto nuevo: no existe esquema. Se crean dos almacenes locales: un archivo SQLite con el registro de
consultas, los fragmentos y su índice de palabras (FTS5), y una carpeta de Qdrant en modo local con los
vectores de los fragmentos ([C-3](requirements.md#c-3)), que además evita recalcular embeddings que no
cambiaron.

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

### ADDED — Colección Qdrant `fragmentos` (modo local)

| Field | Type | Constraints | Classification |
|---|---|---|---|
| id del punto | UUID | UUID v5 de `fragmentos.hash` (idempotente) | interna |
| vector | float[384] | distancia coseno; `paraphrase-multilingual-MiniLM-L12-v2` ([design.md#d4](design.md#d4)) | interna |
| payload `hash` | keyword | igual a `fragmentos.hash`; índice de payload para filtrar | interna |

La colección guarda en su metadata el nombre del modelo de embeddings; si no coincide con la
configuración, se recrea ([design.md#d11](design.md#d11)). Sobrevive a los reinicios y solo recibe
embeddings de hashes nuevos ([NFR-2](requirements.md#nfr-2--arranque)). Carpeta fuera de git.

### MODIFIED — ninguno

### REMOVED — ninguno

## Relationships and indexes

- `fragmentos.id` ↔ `fragmentos_fts.rowid` (1:1).
- `fragmentos.hash` ↔ payload `hash` del punto Qdrant (1:1 tras un arranque exitoso; un punto sin fila en
  `fragmentos` se ignora en la búsqueda y se borra en el siguiente arranque).
- `consultas` no referencia a `fragmentos`: guarda las fuentes como copia, porque el índice se reconstruye
  en cada arranque y el registro debe conservar lo que se respondió.
- Índice sobre `consultas(fecha_hora)` para el historial de MDO-0003.

## Permissions

Archivo SQLite y carpeta de Qdrant locales, de un solo usuario y un solo proceso
([design.md#d13](design.md#d13)); sin roles (`security.md`: sin autenticación en la prueba). Ambos
quedan fuera de git (`.gitignore`).

## State transitions

`consultas.estado` se fija una vez al insertar; no hay transiciones. `BLOQUEADA` queda permitido por el
CHECK pero solo lo escribe MDO-0002.

## Migration

- **Expand:** creación del esquema al arrancar (`CREATE TABLE IF NOT EXISTS`), versión en `PRAGMA user_version = 1`; la colección Qdrant se crea si no existe.
- **Backfill:** no aplica; no hay datos.
- **Contract:** no aplica.
- **Rollback:** borrar la carpeta de Qdrant (se recalculan los embeddings) o el archivo SQLite (el índice
  se reconstruye desde `Data/` y las consultas registradas se pierden; aceptable en la prueba local).

## Evidence

- Sin esquema previo: Premise Ledger [P1](design.md#p1).
