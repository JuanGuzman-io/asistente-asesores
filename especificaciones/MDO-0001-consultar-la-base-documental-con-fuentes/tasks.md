---
schema_version: 1
spec: MDO-0001-consultar-la-base-documental-con-fuentes
status: approved
---

# Tasks — Consultar la base documental con fuentes

Doce tareas en tres entregas, en el orden que fijó el PE: primero la base documental, después la consulta
con validación, falta de información y registro, y al final los errores y el respaldo extractivo. Cada
tarea empieza con pruebas rojas; el modelo y los embeddings se reemplazan por dobles en las pruebas.

## Overview

### Delivery 1 — AC-1, AC-2

#### AC-1 — Documentos oficiales consultables

- [ ] T1 [AC-1] Los documentos oficiales se cargan y fragmentan por sección, sin confidenciales — `pyproject.toml`
- [ ] T3 [AC-1] La base documental queda indexada en SQLite FTS5 y Qdrant local al arrancar — `src/server/infraestructura/busqueda/indice.py`

**Checkpoint:** `uv run pytest tests/server/infraestructura/documentos -q` and `uv run pytest tests/server/infraestructura/busqueda -q` passes (T1, T3); this confirms AC-1 before the next group.

#### AC-2 — Documentos duplicados

- [ ] T2 [AC-2] El contenido duplicado se considera una sola vez, también en las fuentes — `src/server/infraestructura/documentos/cargador.py`

**Checkpoint:** `uv run pytest tests/server/infraestructura/documentos -q` passes (T2); this confirms AC-2 before the next group.

**Delivery checkpoint:** run `mandao run verify-plan <spec> --delivery 1` before delivery 2; it passes when `scope.clear` is true.

### Delivery 2 — AC-3, AC-8, AC-11, AC-6, AC-12, AC-13, AC-5, AC-4, AC-14, AC-7, AC-9, AC-10

#### AC-3, AC-8, AC-11 — Consulta válida con soporte documental; Caracteres especiales; Sin soporte documental

- [ ] T4 [AC-3, AC-8, AC-11] La búsqueda híbrida encuentra la sección correcta o declara que no hay soporte — `src/server/dominio/puertos.py`

**Checkpoint:** `uv run pytest tests/server/infraestructura/busqueda -q` passes (T4); this confirms AC-3, AC-8, AC-11 before the next group.

#### AC-6, AC-11, AC-12, AC-13 — Contenido de cada fuente; Sin soporte documental; Base documental vacía; Pregunta fuera de tema

- [ ] T5 [AC-6, AC-11, AC-12, AC-13] El caso de uso responde con fuentes o con el mensaje fijo de falta de información — `src/server/dominio/estados.py`

**Checkpoint:** `uv run pytest tests/server/aplicacion -q` passes (T5); this confirms AC-6, AC-11, AC-12, AC-13 before the next group.

#### AC-3, AC-5 — Consulta válida con soporte documental; Soporte parcial

- [ ] T6 [AC-3, AC-5] [P] Sin modelo, la respuesta es extractiva y no afirma cubrir toda la pregunta — `src/server/infraestructura/redactor/extractivo.py`

**Checkpoint:** `uv run pytest tests/server/infraestructura/redactor -q` passes (T6); this confirms AC-3, AC-5 before the next group.

#### AC-4, AC-5 — Solo información encontrada; Soporte parcial

- [ ] T7 [AC-4, AC-5] Con Gemini, la respuesta solo usa los fragmentos recuperados y nombra la parte faltante — `src/server/infraestructura/redactor/gemini.py`

**Checkpoint:** `uv run pytest tests/server/infraestructura/redactor -q` passes (T7); this confirms AC-4, AC-5 before the next group.

#### AC-14 — Registro de cada consulta

- [ ] T8 [AC-14] [P] Cada consulta procesada queda registrada completa — `src/server/infraestructura/persistencia/repositorio.py`

**Checkpoint:** `uv run pytest tests/server/infraestructura/persistencia tests/server/aplicacion -q` passes (T8); this confirms AC-14 before the next group.

#### AC-3, AC-7, AC-9, AC-10, AC-14 — Consulta válida con soporte documental; Pregunta vacía o cuerpo inválido; Consulta extensa; Cuerpo o tipo de contenido no admitidos; Registro de cada consulta

- [ ] T9 [AC-3, AC-7, AC-9, AC-10, AC-14] La API de consulta valida la entrada y responde el contrato, con errores RFC 9457 — `src/server/http/app.py`

**Checkpoint:** `uv run pytest tests/server/http -q` passes (T9); this confirms AC-3, AC-7, AC-9, AC-10, AC-14 before the next group.

#### AC-3, AC-4, AC-5, AC-6, AC-11, AC-14 — Consulta válida con soporte documental; Solo información encontrada; Soporte parcial; Contenido de cada fuente; Sin soporte documental; Registro de cada consulta

- [ ] T10 [AC-3, AC-4, AC-5, AC-6, AC-11, AC-14] El flujo crítico pasa de punta a punta y los umbrales quedan calibrados con el dataset — `tests/fixtures/consultas.json`

**Checkpoint:** `uv run pytest tests/server/e2e tests/server/evals -q` passes (T10); this confirms AC-3, AC-4, AC-5, AC-6, AC-11, AC-14 before the next group.

**Delivery checkpoint:** run `mandao run verify-plan <spec> --delivery 2` before delivery 3; it passes when `scope.clear` is true.

### Delivery 3 — AC-16, AC-15

#### AC-16 — Falla del modelo

- [ ] T11 [AC-16] [P] Si Gemini falla, tarda o no está configurado, la respuesta sigue siendo extractiva — `src/server/aplicacion/consultar.py`

**Checkpoint:** `uv run pytest tests/server/aplicacion tests/server/e2e -q` passes (T11); this confirms AC-16 before the next group.

#### AC-15 — Error inesperado

- [ ] T12 [AC-15] [P] Una falla inesperada responde 500 sin exponer detalles internos — `src/server/http/problemas.py`

**Checkpoint:** `uv run pytest tests/server/http -q` passes (T12); this confirms AC-15 before the next group.

**Delivery checkpoint:** run `mandao run verify-plan <spec> --delivery 3`; it passes when `scope.clear` is true.

## Details

### [x] T1 — Los documentos oficiales se cargan y fragmentan por sección, sin confidenciales

- **What:** crea el proyecto backend (Python 3.13 con `uv`, pytest, ruff y mypy estricto) con sus gates
  declarados, y el cargador de `Data/` que excluye confidenciales en dos capas y fragmenta por sección `##`
  ([D1](design.md#d1), [D2](design.md#d2), [D3](design.md#d3), [C-8](requirements.md#c-8)).
- **Done when:**
  - S-1.1 holds: con los seis archivos de `Data/`, hay fragmentos de los cinco oficiales, cada uno con `documento` y `seccion`, y ninguno de `Información restringida.md` (S-1.1/C1).
  - S-1.2 holds: un documento con `CONFIDENCIAL` en sus primeras líneas se excluye aunque no esté en la lista, y el log registra su nombre sin contenido.
  - Un documento sin `##` es un solo fragmento titulado con su `#`.
  - `uv sync` instala con `.python-version` 3.13 y `uv run pytest` corre sin red.
  - `projects[].gates` de `.mandao/config.yml` declara, con aprobación del PE antes de escribirlo, `format: uv run ruff format --check .`, `lint: uv run ruff check .`, `typecheck: uv run mypy src` y `test: uv run pytest`; mypy corre en modo `strict` (configurado en `pyproject.toml`) y los cuatro gates pasan.

```yaml
project: asistente-asesores
kind: feat
tier: standard
files: [pyproject.toml, .python-version, .gitignore, .env.example, .mandao/config.yml, .mandao/mandao.lock, src/server/__init__.py, src/server/config.py, src/server/dominio/modelos.py, src/server/infraestructura/documentos/cargador.py, tests/server/infraestructura/documentos/test_cargador.py]
exemplar: none (proyecto nuevo; este módulo será el exemplar de infraestructura)
ac: [AC-1, AC-1/C1]
scenarios: [S-1.1, S-1.1/C1, S-1.2]
test_levels: { S-1.1: unit, S-1.1/C1: unit, S-1.2: unit }
partial_failure_tests: []
evidence: tdd
risk_tags: [security]
decisions: [D1, D2, D3]
depends_on: []
delivery: 1
parallel_safe: false
verify: uv run pytest tests/server/infraestructura/documentos -q
```

### [x] T2 — El contenido duplicado se considera una sola vez, también en las fuentes

- **What:** el cargador calcula el hash del texto normalizado (minúsculas, espacios colapsados) por
  documento y por fragmento y descarta los repetidos; una regla de dominio deduplica las fuentes por
  `documento > sección` ([D6](design.md#d6), [C-2](requirements.md#c-2)).
- **Done when:**
  - S-2.1 holds: dos archivos con el mismo contenido normalizado producen los fragmentos del primero en orden alfabético y ninguno del segundo, así que no hay dos fuentes con el mismo contenido (S-2.1/C1).
  - S-2.2 holds: dos fragmentos con el mismo `documento > sección` producen una sola fuente.
  - Una sección repetida en dos documentos distintos se indexa una sola vez.
  - Dos secciones parecidas pero distintas (p. ej. "Condiciones" de dos créditos) se conservan ambas.

```yaml
project: asistente-asesores
kind: feat
tier: fast
files: [src/server/infraestructura/documentos/cargador.py, src/server/dominio/reglas.py, tests/server/infraestructura/documentos/test_duplicados.py, tests/server/dominio/test_fuentes.py]
exemplar: src/server/infraestructura/documentos/cargador.py
ac: [AC-2, AC-2/C1]
scenarios: [S-2.1, S-2.1/C1, S-2.2]
test_levels: { S-2.1: unit, S-2.1/C1: unit, S-2.2: unit }
partial_failure_tests: []
evidence: tdd
risk_tags: []
decisions: [D6]
depends_on: [T1]
delivery: 1
parallel_safe: false
verify: uv run pytest tests/server/infraestructura/documentos -q
```

### [x] T3 — La base documental queda indexada en SQLite FTS5 y Qdrant local al arrancar

- **What:** reconstruye `fragmentos` y `fragmentos_fts` en una transacción y sube a Qdrant local solo los
  embeddings nuevos, con un único cliente abierto en el `lifespan` ([D11](design.md#d11),
  [D13](design.md#d13), [data-model.md](data-model.md)).
- **Done when:**
  - S-1.1/C1 holds en el índice: ningún término ni punto de `Información restringida.md` (p. ej. "INT-8457") aparece en FTS5 ni en Qdrant; E2E: el arranque real de la app sobre los seis archivos de `Data/` deja indexados los cinco oficiales y nada del confidencial.
  - Un segundo arranque sin cambios en `Data/` no calcula embeddings (contador del doble de embeddings en 0) y termina en ≤ 2 s con embeddings ya calculados (NFR-2, medido en el log de arranque).
  - Si SQLite falla después del upsert en Qdrant, `fragmentos` conserva el índice anterior y la búsqueda no devuelve puntos huérfanos; los obsoletos se borran solo tras el commit.
  - Cambiar el nombre del modelo de embeddings recrea la colección.
  - La app abre un solo `QdrantClient` y lo cierra al apagar; las pruebas usan una carpeta temporal por prueba.

```yaml
project: asistente-asesores
kind: feat
tier: standard
files: [src/server/infraestructura/busqueda/indice.py, src/server/infraestructura/busqueda/embeddings.py, src/server/infraestructura/busqueda/esquema.py, src/server/http/app.py, tests/server/infraestructura/busqueda/test_indice.py, tests/server/e2e/test_arranque_indice.py]
exemplar: src/server/infraestructura/documentos/cargador.py
ac: [AC-1, AC-1/C1]
scenarios: [S-1.1, S-1.1/C1]
test_levels: { S-1.1: e2e, S-1.1/C1: e2e }
partial_failure_tests: [test_falla_sqlite_tras_upsert_qdrant_conserva_indice_anterior, test_puntos_huerfanos_no_aparecen_en_busqueda]
evidence: tdd
risk_tags: [security, perf]
decisions: [D11, D13]
depends_on: [T2]
delivery: 1
parallel_safe: false
verify: uv run pytest tests/server/infraestructura/busqueda -q
```

### [x] T4 — La búsqueda híbrida encuentra la sección correcta o declara que no hay soporte

- **What:** combina FTS5 (consulta con comillas, sin palabras vacías) y Qdrant por RRF, filtra por hashes
  vigentes y aplica el umbral 0,60 / 0,40 ([D4](design.md#d4), [D5](design.md#d5)).
- **Done when:**
  - S-3.1 holds: "¿Cuál es el monto máximo del Crédito Productivo Impulso?" devuelve primero `Productos de Crédito > Crédito Productivo Impulso`.
  - S-3.2 holds: una pregunta de los cuatro temas sin respuesta en la base no supera el umbral.
  - S-8.1 holds: comillas, paréntesis, `*`, `-`, `:` y emojis no producen error de sintaxis FTS5 (S-8.1/C1); solo signos o emojis omiten la vía FTS.
  - S-8.2 holds: la pregunta sin tildes recupera el mismo fragmento que con tildes.

```yaml
project: asistente-asesores
kind: feat
tier: standard
files: [src/server/dominio/puertos.py, src/server/infraestructura/busqueda/buscador.py, src/server/infraestructura/busqueda/fts.py, tests/server/infraestructura/busqueda/test_buscador.py]
exemplar: src/server/infraestructura/busqueda/indice.py
ac: [AC-3, AC-8, AC-8/C1, AC-11]
scenarios: [S-3.1, S-3.2, S-8.1, S-8.1/C1, S-8.2]
test_levels: { S-3.1: unit, S-3.2: unit, S-8.1: unit, S-8.1/C1: unit, S-8.2: unit }
partial_failure_tests: []
evidence: tdd
risk_tags: [input]
decisions: [D4, D5]
depends_on: [T3]
delivery: 2
parallel_safe: false
verify: uv run pytest tests/server/infraestructura/busqueda -q
```

### [x] T5 — El caso de uso responde con fuentes o con el mensaje fijo de falta de información

- **What:** el caso de uso `consultar` sobre puertos: bajo el umbral o con la base vacía responde el
  mensaje fijo sin llamar al redactor; con soporte arma fuentes `documento`, `seccion`, `fragmento` sin
  repetir ([architecture.md](../../constitucion/architecture.md), [D4](design.md#d4)).
- **Done when:**
  - S-10.1 holds: sin soporte, la respuesta es exactamente "No tengo información suficiente para responder.", `fuentes: []`, estado `Sin información suficiente`, y el doble del redactor no se llama.
  - S-10.2 holds: con la base vacía (carpeta vacía o solo confidenciales) responde lo mismo sin excepción (S-10.2/C1).
  - S-10.3 holds: "¿Va a llover mañana en Bogotá?" da `Sin información suficiente`, nunca `Bloqueada por seguridad` (S-10.3/C1).
  - S-6.1 holds: cada fuente trae `documento`, `seccion` y `fragmento`, deduplicada con la regla de T2, y corresponde a un fragmento que el redactor declaró usado (S-6.1/C1).

```yaml
project: asistente-asesores
kind: feat
tier: standard
files: [src/server/dominio/estados.py, src/server/dominio/modelos.py, src/server/dominio/reglas.py, src/server/aplicacion/consultar.py, tests/server/aplicacion/test_consultar.py]
exemplar: none (proyecto nuevo; será el exemplar de aplicación)
ac: [AC-6, AC-6/C1, AC-11, AC-12, AC-12/C1, AC-13, AC-13/C1]
scenarios: [S-6.1, S-6.1/C1, S-10.1, S-10.2, S-10.2/C1, S-10.3, S-10.3/C1]
test_levels: { S-6.1: eval, S-6.1/C1: unit, S-10.1: unit, S-10.2: unit, S-10.2/C1: unit, S-10.3: unit, S-10.3/C1: unit }
partial_failure_tests: []
evidence: tdd
risk_tags: []
decisions: [D4]
depends_on: [T4]
delivery: 2
parallel_safe: false
verify: uv run pytest tests/server/aplicacion -q
```

### [ ] T6 — Sin modelo, la respuesta es extractiva y no afirma cubrir toda la pregunta

- **What:** `RedactorExtractivo` arma la respuesta con hasta 2 fragmentos sobre el umbral, precedida por
  "Esto es lo que encontré en la base documental:" ([D12](design.md#d12), [C-1](requirements.md#c-1)).
- **Done when:**
  - S-4.1 holds en modo extractivo: la pregunta del PDF responde con estado `Exitosa`, la respuesta contiene `$50.000.000` y trae al menos una fuente (S-4.1/C1).
  - S-5.2 holds: la pregunta por monto y tasa empieza con la frase fija, trae el fragmento del Crédito Productivo Impulso y no afirma responder toda la pregunta ni da una tasa (S-5.2/C1).
  - Cada fragmento va precedido por `Documento > Sección`.

```yaml
project: asistente-asesores
kind: feat
tier: fast
files: [src/server/infraestructura/redactor/extractivo.py, tests/server/infraestructura/redactor/test_extractivo.py]
exemplar: src/server/infraestructura/busqueda/buscador.py
ac: [AC-3, AC-3/C1, AC-5/C2]
scenarios: [S-4.1, S-4.1/C1, S-5.2, S-5.2/C1]
test_levels: { S-4.1: unit, S-4.1/C1: unit, S-5.2: unit, S-5.2/C1: unit }
partial_failure_tests: []
evidence: tdd
risk_tags: []
decisions: [D12]
depends_on: [T5]
delivery: 2
parallel_safe: true
verify: uv run pytest tests/server/infraestructura/redactor -q
```

### [ ] T7 — Con Gemini, la respuesta solo usa los fragmentos recuperados y nombra la parte faltante

- **What:** `RedactorGemini` pide salida JSON con esquema (`respuesta`, `fragmentos_usados`,
  `partes_sin_soporte`) con el prompt versionado v1, y el guardrail de salida en código la valida
  ([D7](design.md#d7), [D9](design.md#d9)).
- **Done when:**
  - S-4.2 holds: una salida con una cifra ausente de los fragmentos citados, o que cita un id no recuperado, o sin `fragmentos_usados`, se descarta y se usa el extractivo (S-4.2/C1).
  - S-5.1 holds: con `partes_sin_soporte: ["la tasa"]`, el código agrega "No encontré información sobre la tasa." y la respuesta no da ni estima una tasa (S-5.1/C1).
  - Si el modelo declara que ninguna parte tiene soporte, el estado es `Sin información suficiente`.
  - La pregunta y los fragmentos van en `contents` delimitados como datos, nunca en `system_instruction`; el prompt vive en `src/server/infraestructura/redactor/prompt.md` v1.
  - Las pruebas usan un doble del cliente de Gemini; ninguna hace llamadas de red.

```yaml
project: asistente-asesores
kind: feat
tier: strong
files: [src/server/infraestructura/redactor/gemini.py, src/server/infraestructura/redactor/validacion.py, src/server/infraestructura/redactor/prompt.md, tests/server/infraestructura/redactor/test_gemini.py, tests/server/infraestructura/redactor/test_validacion.py]
exemplar: src/server/infraestructura/redactor/extractivo.py
ac: [AC-4, AC-4/C1, AC-5, AC-5/C1]
scenarios: [S-4.2, S-4.2/C1, S-5.1, S-5.1/C1]
test_levels: { S-4.2: unit, S-4.2/C1: eval, S-5.1: eval, S-5.1/C1: unit }
partial_failure_tests: []
evidence: tdd
risk_tags: [ai-prompt, security]
decisions: [D7, D9]
depends_on: [T6]
delivery: 2
parallel_safe: false
verify: uv run pytest tests/server/infraestructura/redactor -q
```

### [ ] T8 — Cada consulta procesada queda registrada completa

- **What:** `RepositorioConsultas` en SQLite guarda pregunta, fecha y hora UTC, respuesta, fuentes, estado
  y modo en una transacción antes de responder ([D10](design.md#d10), [data-model.md](data-model.md)).
- **Done when:**
  - S-11.1 holds: una consulta `Exitosa` y otra `Sin información suficiente` quedan con los cinco campos, `fecha_hora` en UTC ISO 8601 y las mismas fuentes que se devolvieron.
  - S-11.2 holds: si el insert falla, el caso de uso propaga el error y no queda ninguna fila parcial.
  - `estado` y `modo` solo aceptan los valores del CHECK; `BLOQUEADA` queda permitido para MDO-0002.

```yaml
project: asistente-asesores
kind: feat
tier: standard
files: [src/server/infraestructura/persistencia/repositorio.py, src/server/infraestructura/persistencia/esquema.py, src/server/aplicacion/consultar.py, tests/server/infraestructura/persistencia/test_repositorio.py]
exemplar: src/server/infraestructura/busqueda/indice.py
ac: [AC-14]
scenarios: [S-11.1, S-11.2]
test_levels: { S-11.1: unit, S-11.2: unit }
partial_failure_tests: [test_falla_insert_consulta_no_deja_fila]
evidence: tdd
risk_tags: [pii]
decisions: [D10]
depends_on: [T5]
delivery: 2
parallel_safe: true
verify: uv run pytest tests/server/infraestructura/persistencia tests/server/aplicacion -q
```

### [ ] T9 — La API de consulta valida la entrada y responde el contrato, con errores RFC 9457

- **What:** la ruta FastAPI con el middleware de `requestId`, 413 y 415, la validación Pydantic (NFC,
  `strip()`, 1–1.000 puntos de código) y los handlers RFC 9457, más el log JSON por petición
  ([D8](design.md#d8), [C-2](requirements.md#c-2)).
- **Done when:**
  - S-7.1 holds: vacía, solo espacios, sin `pregunta`, `pregunta` no texto o JSON mal formado responden 422 `application/problem+json` con `requestId`, sin buscar ni registrar (S-7.1/C1).
  - S-7.2 holds: 1.001 puntos de código responde 422 con el límite en `detail`; 1.000, también con espacios exteriores o en NFD que queda en 1.000 al normalizar, se procesa (S-7.2/C1); el rechazo no recorta, no busca ni registra (S-7.2/C2).
  - S-9.1 y S-9.2 hold: más de 16.384 bytes responde 413, con y sin `Content-Length`; `text/plain` o sin `Content-Type` responde 415; ambos en RFC 9457; tras rechazos con 413, 415 y 422 la tabla `consultas` no tiene filas nuevas (S-11.1/C1).
  - S-14.1 holds: una consulta válida responde 200 con exactamente `respuesta`, `fuentes`, `estado` y la cabecera `X-Request-Id`.
  - NFR-4 holds: cada petición emite una línea JSON con `requestId`, estado o código, `latenciaMs` y número de fuentes, y una prueba sobre los logs capturados no encuentra el texto de la pregunta.

```yaml
project: asistente-asesores
kind: feat
tier: standard
files: [src/server/http/app.py, src/server/http/middleware.py, src/server/http/problemas.py, src/server/http/esquemas.py, src/server/http/rutas.py, src/server/http/logs.py, tests/server/http/test_consultar_api.py, tests/server/http/test_limites.py]
exemplar: src/server/aplicacion/consultar.py
ac: [AC-3, AC-7, AC-7/C1, AC-9, AC-9/C1, AC-9/C2, AC-10, AC-14/C1]
scenarios: [S-7.1, S-7.1/C1, S-7.2, S-7.2/C1, S-7.2/C2, S-9.1, S-9.2, S-14.1, S-11.1/C1]
test_levels: { S-7.1: unit, S-7.1/C1: unit, S-7.2: unit, S-7.2/C1: unit, S-7.2/C2: unit, S-9.1: unit, S-9.2: unit, S-14.1: unit, S-11.1/C1: unit }
partial_failure_tests: []
evidence: tdd
risk_tags: [input, public-api, pii]
decisions: [D8]
depends_on: [T6, T8]
delivery: 2
parallel_safe: false
verify: uv run pytest tests/server/http -q
```

### [ ] T10 — El flujo crítico pasa de punta a punta y los umbrales quedan calibrados con el dataset

- **What:** crea `tests/fixtures/consultas.json` v1 (con respuesta, sin respuesta, fuera de tema y
  parciales sobre `Data/`), la prueba e2e del flujo "Consulta respondida con fuentes y registrada" y las
  evals EV-1 a EV-5; ajusta los umbrales si hace falta ([C-5](requirements.md#c-5), [P5](design.md#p5)).
- **Done when:**
  - S-4.1 holds de punta a punta: la pregunta del PDF responde 200 con `$50.000.000`, su fuente y un registro en `consultas`.
  - Preguntar por "token interno" o "clave temporal" no devuelve nada de `Información restringida.md` (estado `Sin información suficiente` hasta que MDO-0002 agregue el bloqueo).
  - S-10.1 y S-11.1 hold de punta a punta: una pregunta sin soporte responde el mensaje fijo y queda registrada.
  - S-5.2 holds de punta a punta: la pregunta por monto y tasa, sin modelo, empieza con "Esto es lo que encontré en la base documental:" y trae el fragmento con su fuente.
  - EV-1 ≥ 0,90, EV-2 ≥ 0,90, EV-3 ≤ 0,10, EV-4 = 1,00 y EV-5 = 1,00 en modo extractivo; los umbrales finales quedan en configuración y en `design.md` D4.

```yaml
project: asistente-asesores
kind: feat
tier: standard
files: [tests/fixtures/consultas.json, tests/server/e2e/test_flujo_consulta.py, tests/server/evals/test_evals.py, src/server/config.py]
exemplar: tests/server/http/test_consultar_api.py
ac: [AC-3, AC-3/C1, AC-4, AC-5, AC-6, AC-11, AC-14]
scenarios: [S-3.1, S-4.1, S-4.1/C1, S-5.2, S-10.1, S-11.1]
test_levels: { S-3.1: eval, S-4.1: e2e, S-4.1/C1: e2e, S-5.2: e2e, S-10.1: e2e, S-11.1: e2e }
partial_failure_tests: []
evidence: tdd
risk_tags: [perf]
decisions: [D4]
depends_on: [T7, T9]
delivery: 2
parallel_safe: false
verify: uv run pytest tests/server/e2e tests/server/evals -q
```

### [ ] T11 — Si Gemini falla, tarda o no está configurado, la respuesta sigue siendo extractiva

- **What:** el caso de uso pasa al `RedactorExtractivo` ante cualquier excepción, tiempo agotado de 5 s o
  ausencia de `GEMINI_API_KEY`, sin reintentos ([D9](design.md#d9), [D12](design.md#d12)).
- **Done when:**
  - S-12.1 holds: con un doble que lanza error o que no responde antes de 5 s, la consulta responde 200, `Exitosa`, con fragmentos y fuentes, y el registro guarda `modo` `extractivo` (NFR-3).
  - S-12.2 holds: sin `GEMINI_API_KEY` no se crea el cliente de Gemini y la respuesta es extractiva.
  - El cliente de Gemini se configura con `HttpOptions(timeout=5000)` y sin `retry_options`.
  - E2E: con un doble de Gemini caído, el flujo de punta a punta responde 200 extractivo y queda registrado.

```yaml
project: asistente-asesores
kind: feat
tier: standard
files: [src/server/aplicacion/consultar.py, src/server/infraestructura/redactor/gemini.py, src/server/config.py, tests/server/aplicacion/test_respaldo.py, tests/server/e2e/test_respaldo_e2e.py]
exemplar: src/server/aplicacion/consultar.py
ac: [AC-16]
scenarios: [S-12.1, S-12.2]
test_levels: { S-12.1: e2e, S-12.2: unit }
partial_failure_tests: []
evidence: tdd
risk_tags: [ai-prompt]
decisions: [D9, D12]
depends_on: [T10]
delivery: 3
parallel_safe: true
verify: uv run pytest tests/server/aplicacion tests/server/e2e -q
```

### [ ] T12 — Una falla inesperada responde 500 sin exponer detalles internos

- **What:** el handler de `Exception` responde 500 en RFC 9457 con `requestId` y un `detail` genérico, y
  deja el detalle solo en el log ([D8](design.md#d8)).
- **Done when:**
  - S-13.1 holds: si la búsqueda lanza una excepción, responde 500 `application/problem+json` con `requestId` y `detail` genérico.
  - S-13.1/C1 holds: el cuerpo no contiene trazas, rutas, nombres de archivos internos, SQL ni el texto de la pregunta.
  - Si el insert de `consultas` falla (S-11.2), la API responde el mismo 500.
  - El log registra la excepción con `requestId` sin el texto de la pregunta (NFR-4).

```yaml
project: asistente-asesores
kind: feat
tier: fast
files: [src/server/http/problemas.py, src/server/http/app.py, tests/server/http/test_errores.py]
exemplar: src/server/http/problemas.py
ac: [AC-15, AC-15/C1]
scenarios: [S-13.1, S-13.1/C1]
test_levels: { S-13.1: unit, S-13.1/C1: unit }
partial_failure_tests: []
evidence: tdd
risk_tags: [security, public-api]
decisions: [D8]
depends_on: [T9]
delivery: 3
parallel_safe: true
verify: uv run pytest tests/server/http -q
```
