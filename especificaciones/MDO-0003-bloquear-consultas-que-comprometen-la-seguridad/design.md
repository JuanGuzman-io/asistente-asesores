---
schema_version: 1
spec: MDO-0003-bloquear-consultas-que-comprometen-la-seguridad
depth: standard
projects: [asistente-asesores]
status: approved
writes_data: yes
---

# Design — Bloquear consultas que comprometen la seguridad

Un módulo de dominio, `guardrail_entrada`, normaliza la pregunta y evalúa tres familias de expresiones
regulares en un orden fijo; `consultar` lo llama antes de buscar y, si devuelve una categoría, registra y
devuelve el mensaje fijo de bloqueo sin tocar buscador ni redactor. La categoría viaja en `Resultado`
hasta la línea de log; la base de consultas no cambia de esquema.

## Decisions

<a id="d1"></a>
### D1 — El guardrail vive en `dominio` y lo llama `consultar`

- `architecture.md` pone los guardrails en `dominio` y ordena "guardrail de entrada → búsqueda" en
  `aplicacion`. `dominio/guardrail_entrada.py` es una función pura,
  `evaluar_entrada(pregunta) -> CategoriaBloqueo | None`, sin dependencias de otras capas.
- `consultar` es el único camino de la ruta al buscador ([P1](#p1)): ponerlo ahí cubre la API y las
  pruebas del caso de uso con dobles.
- Rechazadas: un puerto `Guardrail` inyectado (DP-9: no hay segunda implementación; las reglas son de
  dominio); un middleware HTTP (dejaría el caso de uso sin protección y duplicaría el registro).

<a id="d2"></a>
### D2 — Reglas: pedidos, no palabras sueltas

Texto normalizado ([D4](#d4)); cada familia es una tupla de `re.Pattern` compilados una vez, con
`\b` en los bordes y sin cuantificadores anidados (NFR-1). Una palabra sensible sola no bloquea: hace
falta un pedido o un calificador interno, que es lo que separa "¿qué hago si un cliente olvida su clave?"
de "¿cuál es la clave temporal?".

| Categoría (`CategoriaBloqueo`) | Bloquea cuando la pregunta… |
|---|---|
| `prompt_injection` | (a) un verbo de anular (`ignora`, `olvida`, `omite`, `descarta`, `salta`, `desobedece`, `anula`, `ignore`, `disregard`, `forget`) seguido, a 0–4 palabras, de `instrucciones`, `prompt`, `lo anterior` o sus equivalentes en inglés, o de `reglas`, `indicaciones`, `restricciones` o `directrices` cuando van con `tus`/`todas` o con `anteriores`/`previas`/`del sistema`/`originales` ("el cliente omite las reglas de pago" no bloquea); (b) cambio de rol: `(ahora\|desde ahora\|a partir de ahora),? (eres\|seras\|actua\|responde)`, `actua como` o `comportate como` al inicio de la pregunta o de una oración, `finge (ser\|que)`, `haz de cuenta que`, `modo (desarrollador\|developer\|administrador\|dios\|sin restricciones)`, `jailbreak`, `(eres\|seas\|seras\|asistente\|modo\|responde\|responder) sin (restricciones\|filtros\|censura\|limites)`; (c) pide el prompt: `prompt del sistema`, `system prompt`, `(muestra\|revela\|repite\|dime\|imprime\|escribe)` a 0–3 palabras de `(tus\|las\|sus) (instrucciones\|reglas)` o de `prompt`; (d) trae un delimitador: `</?(pregunta\|fragmento\|system\|sistema\|instrucciones)\b` o `[/?inst]` |
| `informacion_restringida` | (a) nombra lo reservado: `informacion restringida`, `informacion confidencial`, `documentos? confidencial(es)?`, `informacion tecnologica reservada`, `configuracion(es)? internas?`, `variables? de entorno`, `api[ _]?key`, `clave de (la )?api`, `gemini_api_key`, `\.env\b`; (b) una credencial (`clave`, `contrasena` (y su forma en inglés), `token`, `credencial(es)`, `usuario`) con un calificador interno a 0–4 palabras: `interno/a`, `temporal`, `del sistema`, `de acceso`, `central`, `administrador`, `admin`, `root`, `maestra`, `del servidor`, `de (la )?base de datos`, `de produccion`, `del asistente`; (c) un pedido directo de credencial: `(cual\|cuales) (es\|son) (el\|la\|los\|las\|tu\|tus\|su\|sus)? (clave\|contrasena\|token\|credencial)`, o `(dame\|dime\|muestrame\|revela\|comparte\|pasame\|enviame\|proporciona)` a 0–4 palabras de una credencial |
| `datos_de_clientes` | (a) `(otro\|otra\|otros\|otras) client(e\|es\|a\|as)` con un verbo de pedido (`dame`, `dime`, `muestrame`, `pasame`, `consulta`, `busca`, `revisa`, `trae`, `lista`, `necesito`, `quiero`, `(cual\|cuales) (es\|son)`, `cuanto (debe\|tiene)`); (b) un dato personal (`saldo`, `deuda`, `telefono`, `celular`, `direccion`, `correo`, `cedula`, `numero de cuenta`, `historial`, `movimientos`, `datos personales`, `informacion personal`) junto a un cliente identificado: tratamiento seguido de un nombre (`(senor\|senora\|sr\|sra\|don\|dona) [a-z]{3,}`), `cliente llamad[oa]`, o un número de 6 o más dígitos |

- Orden de evaluación: `prompt_injection`, `informacion_restringida`, `datos_de_clientes`; gana la
  primera que aplica y se registra solo esa.
- Las listas exactas viven en el código; las pruebas por familia y EV-8/EV-9 son su especificación
  ejecutable. Agregar una palabra exige una prueba positiva y que EV-9 siga en 0.
- "A 0–N palabras" admite cualquier puntuación entre palabras (`(?:\W+\w+){0,N}\W+`), y `sr`/`sra`
  admiten punto.
- Excepciones estrechas para AC-4, cada una con su prueba negativa y las positivas que la acotan:
  `las instrucciones para…` no es pedir el prompt; una credencial precedida por `su`/`sus` no toma
  `de acceso` como calificador interno ("un cliente olvida su clave de acceso"); el pedido directo de
  credencial (2c) no aplica si la ventana trae un verbo de trámite en infinitivo (`cambiar`,
  `restablecer`, `recuperar`, `renovar`, `crear`, `generar`, `desbloquear`); un número de 6 o más dígitos
  seguido de `pesos`, `cop`, `millones` o precedido de `$` es un monto, no un identificador; `cc` y
  `c.c.` cuentan como identificador.
- ASSUMPTION(source: PE 2026-10-23, "reglas deterministas"; esta decisión): las reglas no detectan
  ofuscación (letras separadas, homoglifos, otro idioma que no sea inglés) ni un nombre de cliente sin
  tratamiento. La segunda capa cubre ese resto: el documento confidencial no está indexado, la base no
  tiene datos de clientes, el prompt trata la pregunta como datos y el guardrail de salida valida.
  Limitación para el README. Confirma: PE.
- Rechazadas: bloquear por palabra suelta (bloquea "olvida su clave", contra AC-4); un clasificador con
  modelo (DP-4: la seguridad es código; costo y no determinismo); similitud de embeddings contra
  ejemplos (umbral que calibrar, no explicable).

<a id="d3"></a>
### D3 — Mensaje fijo de bloqueo

- `MENSAJE_BLOQUEO = "No puedo responder esta consulta porque no cumple las políticas de seguridad de
  la información."` en `dominio/reglas.py`, junto a `MENSAJE_SIN_INFORMACION`. El mismo para las tres
  categorías; no nombra la regla ni la categoría (AC-1/C1), `fuentes` vacío.
- ASSUMPTION(source: PE 2026-10-23, "mensaje fijo y genérico"): el texto exacto. Confirma: PE.
- Rechazadas: un mensaje por categoría (revela qué regla se activó); sugerir escalar (BR-5 trata la
  incertidumbre, no el bloqueo).

<a id="d4"></a>
### D4 — Normalización propia del guardrail

- `normalizar(texto)`: NFKD, quitar marcas diacríticas (`unicodedata.combining`), `casefold()` y
  colapsar todo espacio en blanco (`\s+` → un espacio) con `strip()`. Así "CLAVE  temporal" y "clave
  temporal" son iguales y `ñ` pasa a `n`. La puntuación se conserva: `\b` y los delimitadores la usan.
- Rechazadas: reutilizar `raices()` de `fts.py` (quita palabras vacías y reduce a raíces: "ignora tus
  instrucciones" pierde la forma que las reglas buscan); `hash_normalizado` del cargador (no quita
  tildes).

<a id="d5"></a>
### D5 — La categoría va al log, no a la base

- `Resultado` gana `categoria: CategoriaBloqueo | None = None` (solo lleno en bloqueos). La ruta la
  pone en `request.state.categoria`; `MiddlewareSolicitud` la pasa a `registrar_peticion`, que añade
  `"categoria"` a la línea JSON solo cuando existe. La línea nunca lleva la pregunta (ya es así, NFR-2).
- El registro en `consultas` es el de siempre: pregunta, fecha y hora, mensaje de bloqueo, `fuentes`
  `[]`, estado `BLOQUEADA`, modo `ninguno` ([P2](#p2)). Sin migración.
- ASSUMPTION(source: PE 2026-10-23, "la categoría va en el log"): no se agrega columna. Confirma: PE.
- Rechazadas: columna `categoria` en `consultas` (migración que nadie pidió; DP-9); guardar la categoría
  dentro de `respuesta` (contamina el dato que ve el asesor).

<a id="d6"></a>
### D6 — Dataset `consultas@v5` y evals deterministas

- s04, s05 y s14 pasan del tipo `sin_respuesta` al tipo nuevo `bloqueada` (CC-1), con
  `estado: "Bloqueada por seguridad"` y `categoria`. Se suman preguntas `bloqueada` hasta tener al
  menos 6 por categoría, y "¿Qué cubre Negocio Seguro?" (`con_respuesta`) y "¿Qué hago si un cliente
  olvida su clave?" (tipo nuevo `sensible`, sin estado esperado salvo no bloquearse). Ninguna pregunta
  trae contenido de `Información restringida.md`.
- EV-8 y EV-9 corren en la suite normal llamando a `evaluar_entrada` sobre el dataset (sin modelo, sin
  red) y en `-m eval` por HTTP. EV-2 excluye `bloqueada` y `sensible`; la prueba de margen C-9 ignora las
  bloqueadas (no pasan por el umbral).
- Rechazadas: un dataset aparte (duplica preguntas y pierde EV-9 sobre las 80 existentes).

## Principle check

| ID | Applies? | Application or reason not applicable |
|---|---|---|
| DP-1 | yes | Bloqueo por defecto de las tres categorías antes de buscar; la entrada ya llega validada por Pydantic. |
| DP-2 | yes | Una bloqueada no tiene fuentes ni contenido documental; el resto del flujo no cambia. |
| DP-3 | yes | Pruebas rojas por familia, de falsos positivos y del registro antes de implementar. |
| DP-4 | yes | La decisión de seguridad es código determinista y revisado; ningún modelo clasifica ni ve la pregunta bloqueada. |
| DP-5 | yes | Una función pura en `dominio`; `aplicacion` la llama; sin dependencias nuevas. |
| DP-6 | yes | Bloquear evita búsqueda, embeddings y llamada al modelo. |
| DP-7 | yes | La bloqueada se persiste y su línea de log suma `categoria`, sin la pregunta. |
| DP-8 | yes | El registro sigue siendo un solo INSERT con commit en `RepositorioConsultasSqlite`. |
| DP-9 | yes | Sin puerto ni clase nuevos: una función, un enum y un campo opcional. |

## Justified exceptions

| Principle | Why the exception is needed | Why a simpler alternative was rejected |
|---|---|---|
| — | — | — |

## Data writes (ACID)

| Operation | Writes committed together | Transaction/tool | Compensation across systems | Concurrency/isolation |
|---|---|---|---|---|
| Registrar consulta bloqueada | Una fila en `consultas` | INSERT parametrizado con commit; rollback y error propagado si falla (MDO-0001 D10) | Ninguna: un solo almacén; si falla, 500 y no hay respuesta | Una conexión SQLite por petición, WAL (sin cambios) |

Prueba de falla parcial: si el registro de una bloqueada falla, la API responde 500 sin el mensaje de
bloqueo ni la pregunta (tarea del caso de uso).

## Model and prompts

| Concern | Choice | Version / reference |
|---|---|---|
| Model | Sin cambios; una bloqueada nunca llega al redactor | `model-registry.md` |
| Prompts | Sin cambios | `src/server/infraestructura/redactor/prompt.md@v1` |
| Chunking / embedding | Sin cambios | MDO-0001 D2, D11 |
| Retrieval (k, filters, reranking) | Sin cambios; no se ejecuta para una bloqueada | MDO-0001 D4 |
| Guardrails | Entrada: `guardrail_entrada` (esta spec). Salida: `validar_salida` existente (segunda capa, PE) | D2; MDO-0001 D7 |
| Fallback | Sin cambios | MDO-0001 D12 |

## Changes by project and module

| Project | Module | Change | Exemplar file |
|---|---|---|---|
| asistente-asesores | `dominio/estados.py` | `CategoriaBloqueo` (StrEnum: `informacion_restringida`, `prompt_injection`, `datos_de_clientes`) | `src/server/dominio/estados.py` |
| asistente-asesores | `dominio/guardrail_entrada.py` (nuevo) | `normalizar`, familias de patrones, `evaluar_entrada` (D2, D4) | `src/server/infraestructura/redactor/validacion.py` |
| asistente-asesores | `dominio/reglas.py`, `dominio/modelos.py` | `MENSAJE_BLOQUEO`; `Resultado.categoria` opcional | `src/server/dominio/reglas.py` |
| asistente-asesores | `aplicacion/consultar.py` | Guardrail antes de buscar; registra y devuelve el bloqueo | `src/server/aplicacion/consultar.py` |
| asistente-asesores | `http/rutas.py`, `http/middleware.py`, `http/logs.py` | `request.state.categoria` → campo `categoria` de la línea JSON | `src/server/http/logs.py` |
| asistente-asesores | `tests/fixtures/consultas.json` | `v5` (D6) | `tests/fixtures/consultas.json` |
| asistente-asesores | `tests/server/` | Unitarias del guardrail y del caso de uso, HTTP del log, e2e `e2e/test_flujo_bloqueo.py`, EV-8/EV-9, ajuste de `test_flujo_consulta.py` y `evals/test_evals.py` | `tests/server/e2e/test_flujo_consulta.py` |

## Diagram

No requerido: un paso nuevo en un flujo existente, un solo proyecto y sin cambio de datos (ver
`mandao run diagram`).

## Contract

Un solo proyecto: el contrato de `POST /api/consultar` no cambia (`estado` ya admite
`Bloqueada por seguridad`).

## Risks and risk tags

- **Falsos positivos** (`security`, `input`): una regla amplia bloquea preguntas legítimas. Mitigación:
  pedidos en vez de palabras (D2), EV-9 en 0 sobre el dataset, casos del PE como pruebas.
- **Evasión** (`security`, `ai-prompt`): reglas fijas no ven ofuscación. Mitigación: segunda capa (D2) y
  limitación documentada.
- **ReDoS** (`perf`, `input`): expresiones con retroceso sobre 1.000 caracteres. Mitigación: sin
  cuantificadores anidados, ventanas acotadas `{0,4}`, NFR-1.
- **Datos personales en logs** (`pii`): la categoría entra al log, la pregunta no. Mitigación: NFR-2.

Tags: `security`, `input`, `ai-prompt`, `pii`, `perf`.

## Constitution Impact

- `critical-flows.md`: la fila "Consulta bloqueada por seguridad" pasa de "OPEN (por crear)" a
  `tests/server/e2e/test_flujo_bloqueo.py` (MDO-0003) e incluye datos de otros clientes.
- `business-rules.md`: BR-4 y BR-8 "Implemented in" `src/server/dominio/guardrail_entrada.py`.
- `security.md`: el threat model nombra las tres categorías y la limitación de D2.
- `model-registry.md`: dataset `consultas@v5` (EV-1 a EV-9).
- `glossary.md`: término "Categoría de bloqueo" (`CategoriaBloqueo`).

## Product Impact

Ninguno en `product.md`. El README (intake I-9) debe listar la limitación de D2.

## Module Docs Impact

- `src/server/AGENTS.md`: `guardrail_entrada`, `MENSAJE_BLOQUEO`, `Resultado.categoria`, campo
  `categoria` del log y flujo "validación → guardrail → búsqueda"; quitar "Nunca devuelve `Bloqueada por
  seguridad`" de `consultar`.

## Premise Ledger

<a id="p1"></a>
### P1 — `consultar` es el único código de `src/` que llama a `buscar` (High)

- **If false:** otro camino llegaría al buscador sin guardrail; habría que ponerlo también ahí (D1).
- **Evidence:** verificada con una corrida registrada ([Evidence](#evidence), P1).

<a id="p2"></a>
### P2 — `consultas` ya acepta estado `BLOQUEADA` y modo `ninguno` sin migración (High)

- **If false:** D5 necesitaría una migración del CHECK.
- **Evidence:** verificada con una corrida registrada ([Evidence](#evidence), P2).

<a id="p3"></a>
### P3 — La línea de log lee sus campos de `scope["state"]`, que la ruta llena (Low)

- **If false:** la categoría necesitaría otro canal hasta `registrar_peticion` (D5).
- **Evidence:** lectura de `src/server/http/middleware.py` (`estado.get("estado")`) y `rutas.py`
  (`request.state.estado`).

<a id="p4"></a>
### P4 — `web` ya muestra `Bloqueada por seguridad` (Low)

- **If false:** la spec tocaría `src/web` y sería multiproyecto.
- **Evidence:** lectura de `src/web/src/api.ts:2` y `Resultado.tsx:11`.

## Evidence

<details><summary>P1 — <code>git grep -n "\.buscar(" -- src</code> (exit 0)</summary>

```
src/server/AGENTS.md:10: … el Protocol `BuscadorDocumental.buscar(pregunta)` …
src/server/aplicacion/consultar.py:33:    busqueda = buscador.buscar(pregunta)
```

Único llamador en código: `consultar.py:33`. Registro en `_log/premises.md`.
</details>

<details><summary>P2 — <code>uv run pytest -q tests/server/infraestructura/persistencia/test_repositorio.py -k "bloqueada or modo"</code> (exit 0)</summary>

```
9 passed, 15 deselected in 0.04s
```

Incluye `test_estado_acepta_los_tres_valores_incluida_bloqueada`. Registro en `_log/premises.md`.
</details>
