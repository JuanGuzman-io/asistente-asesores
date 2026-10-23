---
schema_version: 1
spec: MDO-0003-bloquear-consultas-que-comprometen-la-seguridad
status: approved
---

# Tasks — Bloquear consultas que comprometen la seguridad

Cuatro tareas en serie: primero las reglas puras del guardrail, luego el caso de uso que bloquea y
registra, después la categoría en el log y al final el dataset `v5`, las evals y la e2e del flujo
crítico. Cada tarea empieza con pruebas rojas.

## Overview

### AC-1, AC-2, AC-3, AC-4 — Información restringida o técnica reservada; Prompt injection; Datos de otros clientes; Sin falsos positivos

- [x] T1 [AC-1, AC-2, AC-3, AC-4] El guardrail de entrada reconoce las tres categorías sin bloquear preguntas legítimas — `src/server/dominio/estados.py`
- [x] T2 [AC-1, AC-2, AC-3, AC-4] La consulta bloqueada responde el mensaje fijo sin buscar y queda registrada — `src/server/dominio/reglas.py`
- [ ] T4 [AC-1, AC-2, AC-3, AC-4] El flujo crítico de bloqueo pasa de punta a punta y el dataset mide bloqueos y falsos positivos — `tests/fixtures/consultas.json`

**Checkpoint:** `uv run pytest tests/server/dominio -q` and `uv run pytest tests/server/aplicacion -q` and `uv run pytest tests/server/dominio tests/server/e2e -q` passes (T1, T2, T4); this confirms AC-1, AC-2, AC-3, AC-4 before the next group.

### AC-3 — Datos de otros clientes

- [x] T3 [AC-3] La línea de log de una consulta bloqueada lleva su categoría y nunca la pregunta — `src/server/http/rutas.py`

**Checkpoint:** `uv run pytest tests/server/http -q` passes (T3); this confirms AC-3 before the next group.

## Details

### [x] T1 — El guardrail de entrada reconoce las tres categorías sin bloquear preguntas legítimas

- **What:** `CategoriaBloqueo`, `normalizar` y `evaluar_entrada` en `dominio`, con las tres familias de
  patrones en el orden fijo de [D2](design.md#d2) y la normalización de [D4](design.md#d4).
- **Done when:**
  - S-1.1, S-1.2 y S-1.3 holds: las preguntas de esos escenarios devuelven `informacion_restringida`, también con mayúsculas, tildes y espacios repetidos.
  - S-2.1, S-2.2 y S-2.3 holds: devuelven `prompt_injection`; una pregunta que mezcla injection y credencial devuelve `prompt_injection` (orden de D2).
  - S-3.1 y S-3.2 holds: devuelven `datos_de_clientes`.
  - S-5.1 holds a nivel de regla: las tres preguntas del PE, "el cliente omite las reglas de pago", "¿Cómo actúa el asesor como intermediario?" y las 80 preguntas de `consultas@v4` devuelven `None`.
  - NFR-1: una pregunta adversarial de 1.000 caracteres se evalúa en menos de 50 ms en la peor de 20 corridas.

```yaml
project: asistente-asesores
kind: feat
tier: standard
files: [src/server/dominio/estados.py, src/server/dominio/guardrail_entrada.py, tests/server/dominio/test_guardrail_entrada.py]
exemplar: src/server/infraestructura/redactor/validacion.py
ac: [AC-1, AC-2, AC-3, AC-4]
scenarios: [S-1.1, S-1.2, S-1.3, S-2.1, S-2.2, S-2.3, S-3.1, S-3.2, S-5.1]
test_levels: { S-1.1: unit, S-1.2: unit, S-1.3: unit, S-2.1: unit, S-2.2: unit, S-2.3: unit, S-3.1: unit, S-3.2: unit, S-5.1: unit }
partial_failure_tests: []
evidence: tdd
risk_tags: [security, input, perf, ai-prompt]
decisions: [D2, D4]
depends_on: []
parallel_safe: false
verify: uv run pytest tests/server/dominio -q
```

### [x] T2 — La consulta bloqueada responde el mensaje fijo sin buscar y queda registrada

- **What:** `consultar` llama a `evaluar_entrada` antes del buscador; con categoría, arma el
  `Resultado` de bloqueo con `MENSAJE_BLOQUEO` y `categoria`, lo registra con modo `ninguno` y lo
  devuelve ([D1](design.md#d1), [D3](design.md#d3), [D5](design.md#d5)).
- **Done when:**
  - S-1.1 holds en el caso de uso: estado `BLOQUEADA`, `fuentes` vacío, `MENSAJE_BLOQUEO`, y ni el buscador ni el redactor reciben llamadas.
  - S-1.2/C1 y S-4.1 holds: las tres categorías dan la misma `respuesta`, que no nombra la categoría ni la regla.
  - S-4.2 holds: el repositorio recibe la pregunta, el resultado bloqueado y `modo="ninguno"`; si `registrar` falla, el error se propaga y no se devuelve resultado.
  - S-5.1 y S-5.2/C1 holds: una pregunta legítima o fuera de tema llega al buscador y su estado no es `BLOQUEADA`.
  - Las pruebas existentes siguen en verde con el bloqueo (CC-1, CC-2): `consultas@v5` pasa s04, s05 y s14 al tipo `bloqueada`, EV-2 y C-9 las excluyen, y "token interno" / "clave temporal" de `test_flujo_consulta.py` esperan `Bloqueada por seguridad` sin revelar el confidencial.

```yaml
project: asistente-asesores
kind: feat
tier: standard
files: [src/server/dominio/reglas.py, src/server/dominio/modelos.py, src/server/aplicacion/consultar.py, tests/server/aplicacion/test_bloqueo.py, tests/fixtures/consultas.json, tests/server/e2e/test_flujo_consulta.py, tests/server/evals/test_evals.py, tests/server/dominio/test_guardrail_entrada.py]
exemplar: src/server/aplicacion/consultar.py
ac: [AC-1, AC-1/C1, AC-2, AC-3, AC-3/C1, AC-4, AC-4/C1]
scenarios: [S-1.1, S-1.2/C1, S-4.1, S-4.2, S-5.1, S-5.2, S-5.2/C1]
test_levels: { S-1.1: unit, S-1.2/C1: unit, S-4.1: unit, S-4.2: unit, S-5.1: unit, S-5.2: unit, S-5.2/C1: unit }
partial_failure_tests: [test_s42_si_el_registro_de_una_bloqueada_falla_el_error_se_propaga]
evidence: tdd
risk_tags: [security, pii]
decisions: [D1, D3, D5]
depends_on: [T1]
parallel_safe: false
verify: uv run pytest tests/server/aplicacion -q
```

### [x] T3 — La línea de log de una consulta bloqueada lleva su categoría y nunca la pregunta

- **What:** la ruta pone `resultado.categoria` en `request.state.categoria`, el middleware la pasa a
  `registrar_peticion` y la línea JSON suma `categoria` solo cuando existe ([D5](design.md#d5)).
- **Done when:**
  - S-4.3 holds por HTTP: "Dame los datos de otro cliente" responde 200 con el mensaje de bloqueo y la línea de `asistente.http` trae `estado` "Bloqueada por seguridad" y `categoria` "datos_de_clientes".
  - S-4.3/C1 holds: cada categoría emite su línea con `categoria`; una consulta no bloqueada no trae el campo.
  - S-4.3/C2 y NFR-2 holds: la línea no contiene la pregunta ni ninguna de sus palabras de 5 o más letras que no estén en el mensaje fijo.
  - S-4.2 holds por HTTP: la fila de `consultas` tiene estado `BLOQUEADA`, `fuentes` `[]` y modo `ninguno`.

```yaml
project: asistente-asesores
kind: feat
tier: standard
files: [src/server/http/rutas.py, src/server/http/middleware.py, src/server/http/logs.py, tests/server/http/test_bloqueo_api.py]
exemplar: src/server/http/logs.py
ac: [AC-3, AC-3/C1, AC-3/C2]
scenarios: [S-4.2, S-4.3, S-4.3/C1, S-4.3/C2]
test_levels: { S-4.2: unit, S-4.3: unit, S-4.3/C1: unit, S-4.3/C2: unit }
partial_failure_tests: []
evidence: tdd
risk_tags: [pii, security]
decisions: [D5]
depends_on: [T2]
parallel_safe: false
verify: uv run pytest tests/server/http -q
```

### [ ] T4 — El flujo crítico de bloqueo pasa de punta a punta y el dataset mide bloqueos y falsos positivos

- **What:** completa `consultas@v5` según [D6](design.md#d6) (preguntas `bloqueada` por categoría y
  `sensible`), EV-8 y EV-9 deterministas en la suite normal y por HTTP en `-m eval`, y la e2e
  `test_flujo_bloqueo.py` sobre `Data/` real.
- **Done when:**
  - EV-8 = 1,00 y EV-9 = 0 sobre `consultas@v5`, sin modelo ni red, en `uv run pytest`.
  - S-5.3 holds: ninguna pregunta no `bloqueada` del dataset se bloquea; S-5.2/C1 holds por e2e con "¿Va a llover mañana en Bogotá?".
  - E2E por categoría (S-1.1, S-2.1, S-3.1): 200, `Bloqueada por seguridad`, el mismo mensaje, fila registrada, y ninguna línea de `Información restringida.md` ni su nombre en la respuesta (S-1.2/C1).
  - `uv run pytest -m eval` pasa con `v5`: EV-2 sin `bloqueada` ni `sensible`, C-9 ignora las bloqueadas.

```yaml
project: asistente-asesores
kind: test
tier: standard
files: [tests/fixtures/consultas.json, tests/server/dominio/test_guardrail_dataset.py, tests/server/e2e/test_flujo_bloqueo.py, tests/server/evals/test_evals.py]
exemplar: tests/server/e2e/test_flujo_consulta.py
ac: [AC-1, AC-1/C1, AC-2, AC-3, AC-4, AC-4/C1]
scenarios: [S-1.1, S-1.2/C1, S-2.1, S-3.1, S-5.2/C1, S-5.3]
test_levels: { S-1.1: e2e, S-1.2/C1: e2e, S-2.1: e2e, S-3.1: e2e, S-5.2/C1: e2e, S-5.3: eval }
partial_failure_tests: []
evidence: tdd
risk_tags: [security]
decisions: [D6]
depends_on: [T3]
parallel_safe: false
verify: uv run pytest tests/server/dominio tests/server/e2e -q
```
