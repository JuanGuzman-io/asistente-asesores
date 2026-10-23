# Reviews

## T1 — attempt 1

VERDICT: PASS

La marca `CONFIDENCIAL` ahora se detecta sin importar mayúsculas, como decidió el PE, y la prueba nueva lo demuestra. Ninguno de los cambios bloquea. Me baso en la salida de gates que ejecutó el Leader (`.mandao/cache/MDO-0001/gates/T1-1.md`): format, lint y mypy pasan, y pytest da 9 passed. No volví a ejecutar nada.

**Modelo:** no lo indico. Mi rol me prohíbe decir qué modelo soy, porque Mandao registra quién revisó a partir de lo que invocó.

**Conformidad con la especificación**
- **S-1.2 / D3:** `_es_confidencial` compara con `casefold()` en ambos lados. Sigue mirando solo las 10 primeras líneas (`LINEAS_ENCABEZADO`) y la marca sigue siendo una constante con nombre.
- **El log:** el mensaje no cambió y sigue nombrando el archivo sin su contenido.
- **S-1.1 y AC-1:** busqué "confidencial" en `Data/` sin importar mayúsculas y solo aparece en `Información restringida.md`, línea 4. Ningún documento oficial queda excluido por error con la regla más amplia, y la prueba S-1.1 sigue pasando.

**TDD**
- `execution.md` tiene dos entradas RED. La primera, con exit 127 (`pytest` no encontrado), no sirve como evidencia de rojo. La segunda, con exit 1, sí lo es.
- `redTests.changed` está vacío, así que no se debilitó ninguna prueba en rojo.
- La prueba nueva cubre las dos variantes que faltaban.

**AGENTS.md:** `src/server/AGENTS.md` ya dice "sin distinguir mayúsculas".

**Límites de módulo y código limpio:** sin cambios en importaciones ni en capas, y no hay errores silenciados.

**Seguridad:** no hay hallazgos de seguridad abiertos de severidad alta o crítica. El cambio amplía la exclusión, así que no abre ninguna vía para exponer contenido.

## Findings (JSON)

```json
{"version":1,"findings":[
{"id":"F1","status":"resolved","severity":"low","lens":"security","title":"The CONFIDENCIAL header check matched case-sensitively","file":"src/server/infraestructura/documentos/cargador.py","line":20,"evidence":"Now `MARCA_CONFIDENCIAL.casefold() in linea.casefold()`, as the PE decided on 2026-10-23. test_s12_marca_confidencial_se_detecta_sin_importar_mayusculas covers 'Confidencial' and 'confidencial'. It failed red with exit 1 before the change and passes in the Leader's gate run (9 passed). The substring part of the old F1 is carried over as F7."},
{"id":"F7","status":"open","severity":"low","lens":"security","title":"Header marker still matches as a substring, now in any case","file":"src/server/infraestructura/documentos/cargador.py","line":20,"evidence":"'confidencialidad' or 'Política de confidencialidad' in the first 10 lines would exclude an official document. This fails closed: content is never exposed, but an official document could silently become unavailable, and the log would show it. No file in Data/ is affected today (the only match is 'Información restringida.md', line 4). The PE's decision covered only letter case. Advisory: consider a whole-word match such as re.search(r'\\bconfidencial\\b', linea, re.IGNORECASE)."},
{"id":"F8","status":"open","severity":"low","lens":"core","title":"PE decision not reflected in design.md D3","file":"especificaciones/MDO-0001-consultar-la-base-documental-con-fuentes/design.md","line":1,"evidence":"D3 still says 'la palabra `CONFIDENCIAL`'. The case-insensitive decision is recorded only in _log/execution.md. It does not contradict D3, but the design is the source of truth. Advisory: add the decision and its date to D3. Line number is approximate."},
{"id":"F9","status":"open","severity":"low","lens":"core","title":"New test sets caplog level but asserts nothing on the log","file":"tests/server/infraestructura/documentos/test_cargador.py","line":115,"evidence":"`with caplog.at_level(logging.DEBUG)` has no log assertion. The content-free log is already covered by test_s12_el_log_nombra_el_excluido_y_no_contiene_su_contenido. Advisory: either drop caplog or assert that the excluded file name is logged for the mixed-case variants."}
]}
```

## T2 — attempt 1

VERDICT: PASS

# Revisión de MDO-0001 · T2: deduplicación de contenido y fuentes (intento 1)

T2 queda aprobada: el código cumple AC-2, AC-2/C1, S-2.1, S-2.1/C1, S-2.2 y D6, y la evidencia en rojo basta. Solo hay hallazgos de baja gravedad, ninguno bloqueante.

## Conformidad con la especificación

- **S-2.1 y AC-2 (se cumplen):** `cargar_documentos` recorre `Data/` en orden alfabético con `sorted(directorio.glob("*.md"))`. Descarta un documento cuando su sha256 normalizado (`casefold` y espacios colapsados) ya apareció, y descarta cada fragmento repetido. Gana el primer archivo en orden alfabético.
- **S-2.1/C1 y AC-2/C1 (se cumplen):** el hash por fragmento evita indexar dos veces el mismo contenido. Lo cubre `test_s21_una_seccion_repetida_en_dos_documentos_se_indexa_una_sola_vez`.
- **S-2.2 (se cumple):** `deduplicar_fuentes` deja una sola fuente por `(documento, seccion)`, en orden de primera aparición, con el texto del primer fragmento. `Fuente(documento, seccion, fragmento)` coincide con el contrato de la respuesta 200 en `design.md`.
- **D6, alternativa rechazada (se respeta):** no hay similitud aproximada.
- **Principle check:** DP-1, DP-5 y DP-9 se respetan.

## TDD (`tdd.required: true`)

- **Primer rojo, exit 2:** el `ImportError` de `dominio.reglas` es un rojo válido para `test_fuentes.py`.
- **Segundo rojo, exit 1:** de los cinco casos de `test_duplicados.py`, fallaron cuatro.
- **El caso que pasó en el primer run:** `test_s21_secciones_parecidas_pero_distintas_se_conservan_ambas` es una guarda negativa contra la deduplicación aproximada que D6 rechaza. Revisé sus aserciones de forma independiente: fallaría con dedup aproximada o por `documento > sección` en el cargador. Sirve como evidencia.
- **Cambio en una prueba roja (`test_fuentes.py`):** solo un reordenamiento de imports (I001). No se debilitó ninguna aserción.

## AGENTS.md y estándares

`src/server/AGENTS.md` describe `Fuente`, `reglas.py` y la deduplicación. No encontré errores tragados, números mágicos, nombres fuera del glosario ni lógica duplicada.

## Findings (JSON)

```json
{"version":1,"findings":[
{"id":"F1","status":"open","severity":"low","lens":"core","title":"El hash por fragmento ignora el nombre de la sección: dos secciones distintas con el mismo cuerpo se reducen a una","file":"src/server/infraestructura/documentos/cargador.py","line":68,"evidence":"_hash_normalizado(fragmento.texto) usa solo el cuerpo. Una sección 'Requisitos' de B con el mismo texto que 'Condiciones' de A se descarta y pierde su propia cita. Es literal con D6 ('por fragmento'), así que es advisory; ASSUMPTION: D6 quiso hashear el cuerpo. Si no, conviene aclararlo en design.md."},
{"id":"F2","status":"open","severity":"low","lens":"core","title":"La normalización del hash no aplica NFC al contenido","file":"src/server/infraestructura/documentos/cargador.py","line":20,"evidence":"Los nombres de archivo se normalizan a NFC, pero el texto no. Un mismo documento guardado en NFD y en NFC no se detecta como duplicado. D6 no lo exige (solo minúsculas y espacios), así que es advisory."},
{"id":"F3","status":"open","severity":"low","lens":"core","title":"La salida del run completo de la suite no está en las evidencias","file":".mandao/cache/MDO-0001/gates/T2-1.md","line":42,"evidence":"El gate de tests solo seleccionó los dos archivos nuevos (8 passed, impact confidence medium, sin code graph). Faltó test_cargador.py, que cubre el cargador modificado. El Leader dice que 'pytest tests -q' dio 17 passed, pero esa salida no está en el paquete: OPEN hasta adjuntarla al log de gates."},
{"id":"F4","status":"open","severity":"low","lens":"core","title":"Tier inconsistente entre el brief y execution.md","file":"especificaciones/MDO-0001-consultar-la-base-documental-con-fuentes/_log/execution.md","line":25,"evidence":"El brief dice tier 'fast'; las filas STARTED/RED/REPORTED de T2 dicen 'standard' (y la línea 18 tiene otro STARTED 'fast'). Es un tema de proceso, advisory."}
]}
```

## T3 — attempt 1

VERDICT: FAIL

T3 fails review on two blocking issues, and a third (dependencies) needs a tech-lead decision before it can close:

1. **Duplicated hash rule.** `indice.py` re-implements the content-hash rule (lowercase, collapse spaces, sha256) that the loader already owns.
2. **Qdrant client can be left open at startup.** If the SQLite connection fails, nothing closes the Qdrant client.
3. **Dependencies not approved.** There is no record of the tech lead approving the new dependencies. Some transitive packages use MPL-2.0, which falls outside the allowed licences. No dependency audit was run.

Everything else you asked me to check holds up. I did not run any tests; I rely on the results you reported.

**What I checked**
- **S-1.1 and S-1.1/C1, in the index and the startup log:** both are met. Tests at both levels look for confidential content in FTS5, in the Qdrant payload, in the texts sent to the embeddings double and in the log, and the comparisons don't print confidential content when they fail. The startup log line holds only counts. The exclusion itself comes from T2's loader.
- **D11 order:** correct. Qdrant gets its upsert first (`_subir_nuevos`), then SQLite is rebuilt in one transaction, and only after the commit are stale points deleted. If SQLite fails, the exception rolls back and is re-raised, so the server doesn't start and nothing is deleted. `test_falla_sqlite_tras_upsert_qdrant_conserva_indice_anterior` shows the new point left as an orphan and the old one kept.
- **Hash filter and orphan points:** `test_puntos_huerfanos_no_aparecen_en_busqueda` applies the D11 filter straight to Qdrant, querying with the orphan's exact vector, and the orphan is not returned. The next successful startup cleans it up. The real search is T4's job and the AGENTS.md entry says so.
- **D13, one client:** a single `QdrantClient` lives in the lifespan and is closed on shutdown and when indexing fails. The one gap is finding F2.
- **Embeddings double:** it doesn't hide a real path. `crear_app` has no default, no test imports `EmbeddingsFastembed`, and that class imports fastembed and builds the model only on the first `embeber`. This also means a second startup with no new hashes never loads the ONNX model, which helps NFR-2. ASSUMPTION: the NFR-2 test uses the double, so the ≤ 2 s limit is only proven without the real model.
- **Red tests:** `redTests.changed` is empty and the tester wrote both files. The red runs failed at import, which is valid evidence for new behaviour. No test was weakened.
- **AGENTS.md:** `src/server/AGENTS.md` describes the four new modules.

**Deviations from the spec**
- **Payload index on `hash` removed:** this is reasonable, since local Qdrant doesn't apply payload indexes. But `data-model.md` (line 55) still requires one, so update it.
- **No uvicorn:** this is within T3's scope. OPEN: the design's single-worker uvicorn setup (D13) still has to land in some task.

## Findings (JSON)

```json
{"version":1,"findings":[
{"id":"F1","status":"open","severity":"medium","lens":"core","title":"Duplicated business logic: content hash re-implemented in indice.py","file":"src/server/infraestructura/busqueda/indice.py","line":26,"evidence":"`_hash` repeats `cargador._hash_normalizado` (casefold, collapse spaces, sha256). design.md line 217 gives the hash to the loader (`exclusión, fragmentación, hash`). The UNIQUE constraint on `fragmentos.hash` only holds because the loader deduplicated with exactly the same rule, so if the two copies drift, startup fails. Fix: one function shared by both (a public function in the loader or in dominio)."},
{"id":"F2","status":"open","severity":"medium","lens":"core","title":"D13: QdrantClient is not closed if sqlite3.connect fails","file":"src/server/http/app.py","line":25,"evidence":"`qdrant = QdrantClient(...)` and `conexion = sqlite3.connect(...)` both run before the `try`. If the connect raises (for example, the folder for `ruta_sqlite` doesn't exist), the `finally` never runs and the Qdrant folder stays locked until `__del__`. Fix: open the connection inside the try, or use contextlib.ExitStack, and add a test."},
{"id":"F3","status":"open","severity":"medium","lens":"security","title":"New dependencies without recorded approval; transitive licences outside MIT/Apache/BSD; no audit","file":"uv.lock","line":380,"evidence":"standards.md says the tech lead approves new dependencies and only MIT, Apache-2.0 and BSD licences are allowed. The lock adds fastapi, fastembed, qdrant-client and httpx plus about 45 transitive packages, including certifi (MPL-2.0) and tqdm (MPL-2.0 AND MIT). ASSUMPTION: these licences come from my knowledge of the packages; the lock doesn't record them. The audit gate is not configured and no audit was run, so there is no vulnerability evidence. OPEN: approval or exception from the tech lead."},
{"id":"F4","status":"open","severity":"low","lens":"core","title":"data-model.md still requires the payload index that was removed","file":"especificaciones/MDO-0001-consultar-la-base-documental-con-fuentes/data-model.md","line":55,"evidence":"The implementer dropped the index because local Qdrant doesn't apply it. That is justified, but the spec now disagrees with the code. Record the change (local mode filters by scanning; the index applies when moving to a Qdrant server)."},
{"id":"F5","status":"open","severity":"low","lens":"data","title":"The transaction uses BEGIN, not the BEGIN IMMEDIATE the design specifies","file":"src/server/infraestructura/busqueda/indice.py","line":77,"evidence":"The ACID table in design.md (line 189) specifies `BEGIN IMMEDIATE`. With a single process (D13) there's no practical effect. Advisory: align the code or the design."},
{"id":"F6","status":"open","severity":"low","lens":"core","title":"Model name lives in embeddings.py, not in configuration","file":"src/server/infraestructura/busqueda/embeddings.py","line":4,"evidence":"model-registry.md says 'nombre de modelo fijo en configuración'; the constant `MODELO_EMBEDDINGS` sits in the adapter, not in `config.py`. Advisory."},
{"id":"F7","status":"open","severity":"low","lens":"core","title":"Inconsistent indentation in the pyproject.toml dev group","file":"pyproject.toml","line":17,"evidence":"`\"pytest>=8\"` is indented four spaces and the following entries one. ruff doesn't format TOML, so the gate doesn't catch it. Advisory."},
{"id":"F8","status":"open","severity":"low","lens":"performance","title":"PytestUnraisableExceptionWarning from QdrantClient.__del__ after close","file":"src/server/http/app.py","line":34,"evidence":"The Leader reports it in the full suite run. It looks harmless (a second close in the destructor), but it adds noise to test output. Advisory: confirm it isn't a double close coming from the lifespan."}
]}
```

## T3 — attempt 2

VERDICT: PASS

T3 pasa la revisión en este intento. Los hallazgos bloqueantes F1 y F2 están corregidos. F3 tiene la decisión del PE registrada en `execution.md`. F5, F6 y F7 están resueltos, y la explicación de F8 coincide con el código. Siguen abiertos dos puntos menores que no bloquean: F4, el cambio pendiente en `data-model.md`, y F9, cómo dejar constancia del riesgo aceptado de pillow. No ejecuté pruebas. Me baso en la salida de gates del intento 2 (`.mandao/cache/MDO-0001/gates/T3-2.md`: 12 passed y 2 warnings en el run de impacto) y en lo que dice el Leader sobre la suite completa (29 passed, 2 warnings). Esa suite completa no la vi.

**Hallazgos anteriores**
- **F1, resuelto.** `cargador.hash_normalizado` es ahora pública e `indice.py` la importa. Ya no queda ninguna copia en el código de producción. El `_hash` de `test_indice.py` es un oráculo independiente de la prueba: si la regla cambiara, la prueba detectaría la divergencia. Es aceptable.
- **F2, resuelto.** En `app.py`, `sqlite3.connect` y `cargar_documentos` están ahora dentro del `try`. El `finally` cierra la conexión solo si se llegó a abrir, y siempre cierra `qdrant`. La prueba nueva `test_d13_si_falla_la_conexion_sqlite_el_cliente_qdrant_se_cierra` está registrada en rojo con exit 1, es decir, falló por aserción y no por import. La prueba es válida: con el código anterior la excepción saltaba antes del `try` y `cierres` quedaba vacío. La lista `aperturas` conserva una referencia al cliente, así que `__del__` no puede ejecutar `close` por su cuenta y enmascarar el fallo. La prueba también comprueba que la carpeta queda desbloqueada.
- **F3, resuelto por decisión del PE (2026-10-23).** La decisión está en la fila REPORTED del intento 2 (`execution.md`, línea 36): dependencias aprobadas, excepción de licencias MPL-2.0/PSF-2.0 para transitivas sin modificar y aceptación del riesgo de pillow. `pip-audit-t3.txt` confirma 35 avisos, todos de pillow 12.3.0 y todos con arreglo en 13.0.0 (34 CVE y un GHSA; las notas dicen "35 CVE", diferencia menor). Desde la lente de seguridad el argumento se sostiene: `EmbeddingsFastembed` solo pasa texto a `TextEmbedding` y la app no decodifica imágenes. Lo que queda está en F9.
- **F4, sigue abierto (low).** Es un cambio de spec y, como dice el Leader, queda para verify o close con aprobación humana.
- **F5, resuelto.** `_reconstruir_sqlite` ejecuta `BEGIN IMMEDIATE`. `crear_esquema` hace commit antes, así que no hay ninguna transacción abierta cuando se emite. La prueba de fallo parcial demuestra el rollback.
- **F6, resuelto.** `MODELO_EMBEDDINGS` está en `config.py` y `embeddings.py` lo importa de ahí.
- **F7, resuelto.** El grupo dev de `pyproject.toml` tiene ahora una sangría uniforme.
- **F8, resuelto.** El lifespan llama a `qdrant.close()` una sola vez, en el `finally`. En `qdrant_client.py`, `__del__` (línea 171) llama otra vez a `close()`, y `QdrantLocal.close` no es idempotente. La traza del gate termina en `sqlite3.ProgrammingError: SQLite objects created in a thread can only be used in that same thread`: el cliente se crea en el hilo del portal de TestClient y el GC lo destruye desde el hilo principal. Es ruido de la librería, no un doble cierre de la app.

**Comprobaciones en este intento**
- **S-1.1 y S-1.1/C1:** no hay cambios de lógica respecto al intento 1. Las pruebas en ambos niveles siguen buscando contenido confidencial en FTS5, en el payload de Qdrant, en el doble de embeddings y en el log.
- **Orden de D11:** intacto. Primero el upsert en Qdrant, después la transacción SQLite y, solo tras el commit, el borrado de obsoletos.
- **TDD:** `redTests.changed` está vacío. Hay evidencia en rojo para los dos archivos en el intento 1 y para el e2e en el intento 2. No se debilitó ninguna prueba.
- **AGENTS.md:** `src/server/AGENTS.md` describe `hash_normalizado` como la regla única, además de `embeddings.py`, `esquema.py`, `indice.py` y `app.py`.
- **Límites entre módulos:** `busqueda/indice.py` usa la función pública del cargador, no su interior. Correcto.
- **OPEN, igual que en el intento 1:** uvicorn con un solo worker (D13) todavía tiene que llegar en alguna tarea.

## Findings (JSON)

```json
{"version":1,"findings":[
{"id":"F1","status":"resolved","severity":"medium","lens":"core","title":"Duplicated business logic: content hash re-implemented in indice.py","file":"src/server/infraestructura/busqueda/indice.py","line":18,"evidence":"indice.py imports `hash_normalizado` from cargador.py (now public); no copy of the rule remains in production code. AGENTS.md says it is the single rule."},
{"id":"F2","status":"resolved","severity":"medium","lens":"core","title":"D13: QdrantClient is not closed if sqlite3.connect fails","file":"src/server/http/app.py","line":27,"evidence":"`sqlite3.connect` now runs inside the try; the finally always calls `qdrant.close()`. Red test `test_d13_si_falla_la_conexion_sqlite_el_cliente_qdrant_se_cierra` recorded in RED (exit 1) in attempt 2 and PASS in the attempt 2 gates."},
{"id":"F3","status":"resolved","severity":"medium","lens":"security","title":"New dependencies without recorded approval; transitive licences outside MIT/Apache/BSD; no audit","file":"uv.lock","line":1,"evidence":"PE decision 2026-10-23 recorded in execution.md (T3 attempt 2 REPORTED): dependencies approved; licence exception MPL-2.0/PSF-2.0 for unmodified transitive packages for all of MDO-0001; pip-audit run (35 advisories, all pillow 12.3.0, fixed in 13.0.0) and risk accepted. Follow-up in F9."},
{"id":"F4","status":"open","severity":"low","lens":"core","title":"data-model.md still requires the payload index that was removed","file":"especificaciones/MDO-0001-consultar-la-base-documental-con-fuentes/data-model.md","line":55,"evidence":"Unchanged. Spec change deferred to verify/close with human approval per the Leader. Non-blocking for T3."},
{"id":"F5","status":"resolved","severity":"low","lens":"data","title":"The transaction uses BEGIN, not the BEGIN IMMEDIATE the design specifies","file":"src/server/infraestructura/busqueda/indice.py","line":73,"evidence":"`_reconstruir_sqlite` now executes `BEGIN IMMEDIATE`; `crear_esquema` commits beforehand, so no nested transaction."},
{"id":"F6","status":"resolved","severity":"low","lens":"core","title":"Model name lives in embeddings.py, not in configuration","file":"src/server/config.py","line":5,"evidence":"`MODELO_EMBEDDINGS` moved to config.py; embeddings.py imports it."},
{"id":"F7","status":"resolved","severity":"low","lens":"core","title":"Inconsistent indentation in the pyproject.toml dev group","file":"pyproject.toml","line":12,"evidence":"Dev group entries now consistently indented with four spaces."},
{"id":"F8","status":"resolved","severity":"low","lens":"performance","title":"PytestUnraisableExceptionWarning from QdrantClient.__del__ after close","file":"src/server/http/app.py","line":38,"evidence":"Lifespan calls `qdrant.close()` exactly once. The warning comes from `QdrantClient.__del__` (qdrant_client.py:171) calling the non-idempotent `QdrantLocal.close` again during GC on the main thread; the traceback ends in sqlite3.ProgrammingError (check_same_thread) because the client was created on the TestClient portal thread. Library noise, not an app double close."},
{"id":"F9","status":"open","severity":"low","lens":"security","title":"Accepted pillow 12.3.0 risk lives only in execution.md, with no revisit trigger and no audit gate","file":"constitucion/standards.md","line":62,"evidence":"pip-audit-t3.txt: 35 advisories in pillow 12.3.0 (fix 13.0.0), blocked by fastembed 0.9.0 requiring pillow<13. The PE accepted the risk (text-only use). Advisory: when standards.md is updated at close, also record the pillow acceptance with a revisit trigger (upgrade once fastembed allows pillow>=13), and configure the `audit` gate (currently not configured) so regressions surface automatically."}
]}
```
