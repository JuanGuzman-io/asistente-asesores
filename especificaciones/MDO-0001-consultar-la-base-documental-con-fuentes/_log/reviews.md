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

## T4 — attempt 1

VERDICT: FAIL

Reviso T4, intento 1. Hay un hallazgo bloqueante: la asunción del implementador hace que no se cumpla la regla de umbral de D4. El resto de lo que pediste revisar está bien: el SQL va con parámetros, los umbrales están en config, el rojo es válido y `test_indice.py` no quedó más débil.

## Asunción "solo por FTS ⇒ coseno 0" frente a D4 (bloqueante)

D4 dice: "hay soporte si **el mejor fragmento** tiene similitud coseno ≥ `UMBRAL_ALTO` (0,60), o ≥ `UMBRAL_BAJO` y además coincide en FTS". En design.md no hay nada que autorice poner a 0 el coseno real de un fragmento.

Además, el efecto es más amplio de lo que parece:
- **Cuándo pasa.** Con RRF (k = 60), un fragmento que sale en las dos vías suma como mínimo 2/65 ≈ 0,0308. Uno que sale en una sola vía suma como máximo 1/61 ≈ 0,0164. Por eso un fragmento solo de FTS únicamente queda primero cuando los 5 de FTS y los 5 de Qdrant no tienen ninguno en común.
- **El empate.** En ese caso, el primero de FTS y el primero de Qdrant empatan exactamente en 1/61. `sorted(...)` es estable y `puntaje` recibe primero los hashes de FTS (`for ranking in (por_fts, list(cosenos))`), así que el empate siempre lo gana el de FTS. Su coseno pasa a 0 y el resultado es "sin soporte".
- **Consecuencia.** Siempre que las dos listas no compartan ningún fragmento, la respuesta es "sin soporte" aunque Qdrant tenga un candidato con coseno 0,95. Esto anula la vía de "≥ 0,60 basta", que D4 justifica justamente porque solo FTS falla con sinónimos. Falla del lado prudente (AC-11), pero produce falsos "Sin información suficiente" en AC-3.
- **Ninguna prueba lo cubre.**

**Arreglo propuesto:** usar el coseno real del mejor fragmento cuando no esté entre los 5 de Qdrant (por ejemplo, `query_points` con filtro `hash == mejor` y `limit=1`). Además: añadir una prueba con las dos listas sin fragmentos en común, donde el candidato de Qdrant tenga coseno ≥ 0,60, y actualizar la línea de `src/server/AGENTS.md` que documenta la asunción.

## Lo demás que pediste revisar

- **La pregunta nunca se interpola en el SQL (lente security): cumple.** `buscar_fts` usa `MATCH ?` y `LIMIT ?` con parámetros. `_existe` y `_fragmento` también usan `?`. `consulta_fts` solo deja pasar `[a-z0-9]+` sin tildes, cita cada palabra y las une con `OR`. Cuando no queda ninguna palabra útil devuelve `None` y no se ejecuta ningún MATCH. Las pruebas lo cubren con 23 entradas hostiles, con el trace callback y con "NOT como palabra". No hay hallazgos de seguridad abiertos.
- **Filtro de huérfanos: funciona, pero con una diferencia de diseño** (medio, no bloqueante). Filtra después de `limit=5`, así que cada huérfano le quita un sitio a un candidato vigente. design.md pide "filtro por hashes vigentes" y la prueba de T3 usa `query_filter` con `MatchAny`.
- **Umbrales en config: cumple.** `UMBRAL_ALTO` y `UMBRAL_BAJO` están en `config.py` y se inyectan como valores por defecto del constructor. `CANDIDATOS`, `RESULTADOS` y `K_RRF` son constantes con nombre.
- **Fusión RRF: el cálculo es correcto (k = 60, top 3), pero la prueba es débil** (medio). En `test_s31_rrf_conserva_el_orden...` BM25 y los cosenos ordenan igual. Falta un caso donde los dos órdenes sean distintos.
- **Movimiento de fixtures: no debilitó `test_indice.py`.** Las fixtures pasaron idénticas a `conftest.py`; `test_indice.py` solo pierde imports sin uso; sus 7 pruebas pasan.
- **TDD: cumple.** El rojo está registrado (exit 2, error de recolección). El único cambio sobre las pruebas rojas es el orden de imports (I001). ASSUMPTION: no tengo el archivo rojo original para compararlo.
- **Sección no embebida: es de calibración, no de T4.** Queda como observación abierta.
- **Evidencia de las pruebas.** En `.mandao/cache/MDO-0001/gates/T4-1.md` solo consta `34 passed`. No hay salida que muestre los "56 passed" de la suite completa (OPEN). El gate `audit` aparece como SKIPPED aunque está configurado.

## Findings (JSON)

```json
{"version":1,"findings":[
{"id":"F1","status":"open","severity":"high","lens":"core","title":"Coseno 0 para el mejor fragmento que llega solo por FTS contradice D4 y, con el desempate estable a favor de FTS, anula el umbral alto cuando las dos vías no comparten candidatos","file":"src/server/infraestructura/busqueda/buscador.py","line":442,"evidence":"`coseno = cosenos.get(mejor, 0.0)`. Si FTS y Qdrant no comparten candidatos, el primero de cada vía empata en 1/61 y `sorted` estable sobre `puntaje` (rellenado primero con por_fts) elige el de FTS, así que hay_soporte=False aunque el primero de Qdrant tenga coseno >= 0,60. D4 exige el coseno real del mejor fragmento. Ninguna prueba cubre listas sin candidatos en común."},
{"id":"F2","status":"open","severity":"medium","lens":"core","title":"El filtro de huérfanos se aplica después de limit=5 y reduce los candidatos vigentes de la vía vectorial","file":"src/server/infraestructura/busqueda/buscador.py","line":453,"evidence":"query_points(limit=CANDIDATOS) sin query_filter y después `_existe` por punto. design.md: '5 por vía ... filtro por hashes vigentes'. La prueba de T3 usa Filter(MatchAny) en Qdrant."},
{"id":"F3","status":"open","severity":"medium","lens":"core","title":"La prueba de RRF no distingue la fusión de un orden por una sola vía","file":"tests/server/infraestructura/busqueda/test_buscador.py","line":765,"evidence":"BM25 y los cosenos ordenan igual (0.9..0.5 y 'comun' x5..x1), así que ordenar solo por coseno o solo por BM25 también pasaría. Falta un caso con órdenes distintos y uno sin candidatos en común (ver F1)."},
{"id":"F4","status":"open","severity":"low","lens":"core","title":"No hay evidencia registrada de la suite completa (56 passed) y audit aparece como SKIPPED","file":".mandao/cache/MDO-0001/gates/T4-1.md","line":51,"evidence":"La salida del gate test muestra 'collected 34 items ... 34 passed' (solo busqueda/). audit está configurado en el brief pero figura como SKIPPED."},
{"id":"F5","status":"open","severity":"low","lens":"ai","title":"Solo se embebe `texto`, no `seccion`: posible efecto en S-3.1 con el modelo real","file":"src/server/infraestructura/busqueda/indice.py","line":60,"evidence":"embeddings.embeber([texto ...]). Es una decisión de T3 y debe calibrarse contra EV-2/EV-3 (P5). No bloquea T4."},
{"id":"F6","status":"resolved","severity":"low","lens":"security","title":"La pregunta nunca se interpola en el SQL; las entradas hostiles no producen errores de sintaxis FTS5","file":"src/server/infraestructura/busqueda/fts.py","line":508,"evidence":"`MATCH ?` y `LIMIT ?` con parámetros; solo pasan tokens [a-z0-9]+ citados; None salta el MATCH; cubierto por test_s81_c1_* y test_s81_solo_signos_*."},
{"id":"F7","status":"resolved","severity":"low","lens":"core","title":"El movimiento de fixtures a conftest.py no debilita test_indice.py","file":"tests/server/infraestructura/busqueda/conftest.py","line":1,"evidence":"Las fixtures conexion/qdrant/oficiales son idénticas; test_indice.py solo pierde imports sin uso; sus 7 pruebas pasan en la salida del gate."}
]}
```

## T4 — attempt 2

VERDICT: PASS

# Revisión de MDO-0001 · T4, intento 2

T4 se puede aceptar. Los dos hallazgos que bloqueaban en el intento 1 (F1 y F2) están corregidos y cada uno tiene una prueba que falló antes del arreglo. F3 y F4 también quedan resueltos. F5 sigue abierto como tarea de calibración; no es de T4. Quedan dos observaciones nuevas de severidad baja que no bloquean.

## Estado de los hallazgos del intento 1

- **F1, coseno del mejor fragmento (resuelto).** Cuando el mejor fragmento no está entre los 5 de Qdrant, `_coseno_de` busca su coseno real en Qdrant con el filtro `hash == mejor` y `limit=1`. Solo usa 0 si el fragmento no está indexado, y eso es lo que pide D4. La prueba `test_d4_sin_candidatos_comunes_usa_el_coseno_real_del_mejor_fragmento` reproduce el problema: las dos vías no comparten candidatos, A (coseno 0,65) empata con B1 en 1/61 y gana el desempate por FTS; con el código anterior su coseno pasaba a 0 y el resultado era "sin soporte"; con el arreglo hay soporte. El rojo está registrado en el intento 2 (exit 1).
- **F2, huérfanos que quitaban cupos (resuelto).** `query_filter` con `MatchAny(any=vigentes)` se aplica dentro de la consulta a Qdrant, antes del `limit`. La prueba `test_d11_los_huerfanos_no_quitan_cupos_a_los_candidatos_vigentes` usa 6 huérfanos con coseno 1 y un vigente con 0,7. Falló antes del arreglo.
- **F3, prueba de la fusión RRF (resuelto).** Pasó desde la primera ejecución, sin evidencia de mutación; revisé las aserciones de forma independiente según `loop.evidenceOptions`. Puntajes rehechos a mano: S0 0,031778; S1 0,032002; S2 0,032266; S3 0,031754; S4 0,031010. La fusión da S2, S1, S0; solo BM25 daría S0, S1, S2; solo coseno, S2, S3, S1; k = 0 daría S2, S0, S1. La prueba fija también el orden de BM25 con `buscar_fts`. Basta como evidencia de que discrimina.
- **F4, evidencia de la suite completa (resuelto).** La salida guardada termina en `59 passed, 2 warnings in 1.21s`. El gate `test` de T4-2.md muestra `37 passed`. `audit` en SKIPPED es aceptable: T4 no toca `pyproject.toml` ni `uv.lock`.
- **F5 (sigue abierto).** Calibración EV-2/EV-3 (P5); no bloquea T4.
- **F6 y F7 (siguen resueltos).** La pregunta sigue sin interpolarse en el SQL; el nuevo filtro de Qdrant solo recibe hashes leídos de `fragmentos`. Mover las fixtures no debilitó `test_indice.py`.

## Otras comprobaciones

- **TDD:** `redTests.changed` está vacío y el rojo del intento 2 está registrado. No se debilitó ninguna prueba roja.
- **AGENTS.md:** describe el filtro por hashes vigentes y la consulta del coseno real; ya no menciona la asunción del coseno 0.
- **Límites entre módulos:** sin violaciones de `architecture.md`.

## Observaciones nuevas (no bloquean)

- **F8.** `_coseno_de` vuelve a calcular el embedding de la pregunta. Mejora sugerida: reutilizar el vector. OPEN: no se probó `MatchAny(any=[])` con `fragmentos` vacía.
- **F9.** `PytestUnraisableExceptionWarning` de un `QdrantClient` cerrado desde otro hilo. ASSUMPTION: viene del lifespan de la prueba e2e de T3. Revisar fuera de T4.

## Findings (JSON)

```json
{"version":1,"findings":[
{"id":"F1","status":"resolved","severity":"high","lens":"core","title":"Coseno 0 para el mejor fragmento que llega solo por FTS contradice D4","file":"src/server/infraestructura/busqueda/buscador.py","line":441,"evidence":"Ahora `coseno = cosenos[mejor] if mejor in cosenos else self._coseno_de(pregunta, mejor)`; `_coseno_de` hace query_points con Filter(hash == mejor), limit=1. Cubierto por test_d4_sin_candidatos_comunes_usa_el_coseno_real_del_mejor_fragmento (rojo registrado en el intento 2): A (coseno .65) gana el empate 1/61 contra B1 y da soporte."},
{"id":"F2","status":"resolved","severity":"medium","lens":"core","title":"El filtro de huérfanos se aplicaba después de limit=5","file":"src/server/infraestructura/busqueda/buscador.py","line":456,"evidence":"query_filter=Filter(must=[FieldCondition(key='hash', match=MatchAny(any=vigentes))]) dentro de query_points. Cubierto por test_d11_los_huerfanos_no_quitan_cupos_a_los_candidatos_vigentes (6 huérfanos con coseno 1, el vigente con .7; rojo registrado)."},
{"id":"F3","status":"resolved","severity":"medium","lens":"core","title":"La prueba de RRF no distinguía la fusión de un orden por una sola vía","file":"tests/server/infraestructura/busqueda/test_buscador.py","line":788,"evidence":"Revisión independiente de las aserciones: puntajes RRF rehechos a mano (S2 .032266, S1 .032002, S0 .031778, S3 .031754, S4 .031010). La fusión da S2,S1,S0; solo BM25 daría S0,S1,S2; solo coseno, S2,S3,S1; k=0 daría S2,S0,S1. La prueba fija además el orden BM25 con buscar_fts."},
{"id":"F4","status":"resolved","severity":"low","lens":"core","title":"No había evidencia de la suite completa y audit aparecía como SKIPPED","file":".mandao/cache/MDO-0001/gates/T4-2.md","line":51,"evidence":"T4-2-fullsuite.txt: '59 passed, 2 warnings in 1.21s'. Gate test: 37 passed. audit se salta por diseño del runner: T4 no cambia dependencias (el manifiesto no incluye pyproject.toml ni uv.lock)."},
{"id":"F5","status":"open","severity":"low","lens":"ai","title":"Solo se embebe `texto`, no `seccion`: posible efecto en S-3.1 con el modelo real","file":"src/server/infraestructura/busqueda/indice.py","line":60,"evidence":"Decisión de T3, pendiente de calibrar contra EV-2/EV-3 (P5). No bloquea T4."},
{"id":"F6","status":"resolved","severity":"low","lens":"security","title":"La pregunta nunca se interpola en el SQL; las entradas hostiles no producen errores de sintaxis FTS5","file":"src/server/infraestructura/busqueda/fts.py","line":515,"evidence":"`MATCH ?` y `LIMIT ?` con parámetros; solo pasan tokens [a-z0-9]+ citados. El nuevo filtro de Qdrant solo recibe hashes leídos de `fragmentos`, nunca texto del usuario."},
{"id":"F7","status":"resolved","severity":"low","lens":"core","title":"El movimiento de fixtures a conftest.py no debilita test_indice.py","file":"tests/server/infraestructura/busqueda/conftest.py","line":1,"evidence":"Fixtures idénticas; las 7 pruebas de test_indice.py pasan en el gate del intento 2."},
{"id":"F8","status":"open","severity":"low","lens":"performance","title":"_coseno_de vuelve a calcular el embedding de la pregunta","file":"src/server/infraestructura/busqueda/buscador.py","line":464,"evidence":"Se llama a embeddings.embeber([pregunta]) en _buscar_vectores y otra vez en _coseno_de. Mejora sugerida: reutilizar el vector. OPEN: no se probó MatchAny(any=[]) con `fragmentos` vacía."},
{"id":"F9","status":"open","severity":"low","lens":"core","title":"Aviso de QdrantClient cerrado desde otro hilo en la suite completa","file":"tests/server/e2e/test_arranque_indice.py","line":1,"evidence":"PytestUnraisableExceptionWarning: 'SQLite objects created in a thread can only be used in that same thread' en QdrantClient.__del__, que salta durante test_s31_rrf_fusiona_*. ASSUMPTION: viene del cliente que abre el lifespan de la prueba e2e de T3; no es código de T4."}
]}
```

## T5 — attempt 1

VERDICT: PASS

# Review de MDO-0001 · T5, intento 1

T5 cumple su "Done when". El caso de uso respeta las capas de `architecture.md` y cada escenario de la tarea tiene una prueba que lo verifica. No hay hallazgos que bloqueen. Hay un hallazgo de severidad media que conviene corregir en `src/server/AGENTS.md`: atribuye a T6 el guardrail D7, que es de T7.

## Conformidad con la spec

- **S-10.1 / AC-11.** Sin soporte, la respuesta es el mensaje fijo exacto, con `fuentes == []` y estado `Sin información suficiente`, y el redactor no se llama. Las pruebas lo comprueban, incluido el caso con fragmentos candidatos bajo el umbral, y que `MENSAJE_SIN_INFORMACION` coincide con el texto del PDF.
- **S-10.2 / S-10.2/C1 / AC-12.** Con la base vacía responde lo mismo y no lanza excepción; el buscador inconsistente (`hay_soporte=True` sin fragmentos) también da el mensaje fijo. "El servidor arranca" no es de esta capa.
- **S-10.3 / C1 / AC-13.** "¿Va a llover mañana en Bogotá?" da `Sin información suficiente` y nunca `Bloqueada por seguridad`.
- **S-6.1 / S-6.1/C1 / AC-6.** Cada fuente trae `documento`, `seccion` y `fragmento`, deduplicadas con `deduplicar_fuentes` y solo de los fragmentos declarados usados. Solo la parte determinista, dentro del alcance acordado.
- **D4.** Bajo el umbral no se llama al modelo.

## Límites de módulo y Principle check

`aplicacion/consultar.py` solo importa de `dominio`; DP-5 y DP-9 se cumplen. Nombres según `glossary.md`. Sin errores tragados que bloqueen, números mágicos ni lógica duplicada (ver F2).

## TDD (ADR 0022)

- Rojo registrado (línea 46 de `execution.md`, exit 2 por falta de `src.server.aplicacion`).
- `redTests.changed` lista `test_consultar.py`; según el log, solo `ruff --fix` I001. Sin aserciones debilitadas. ASSUMPTION: no tengo shell para comparar con el archivo del rojo.
- Pruebas significativas, sobre comportamiento observable, con dobles de los puertos.
- Gates T5-1 en PASS; suite completa 74 passed (T5-1-fullsuite.txt). El warning de `QdrantClient.__del__` viene de T4 (F5).

## Decisiones de API

| Decisión | Dictamen |
|---|---|
| Ids de `fragmentos_usados` 1-based | Confirmada. Encaja con D7. T7 debe numerar desde 1 y validar igual. |
| Fuentes en el orden de recuperación | Confirmada (D6, DP-4). |
| Ids fuera de rango se ignoran | Confirmada solo en `consultar`, con salvedades (F1, F2). El guardrail D7 es de **T7**. |
| `partes_sin_soporte=()` sin uso | Confirmada. Lo consume **T7**. |
| `Estado` es `StrEnum` | Confirmada; el docstring de la prueba sigue diciendo `(str, Enum)` (F4). |

## Findings (JSON)

```json
{"version":1,"findings":[
{"id":"F1","status":"open","severity":"medium","lens":"core","title":"AGENTS.md atribuye a T6 el guardrail de salida D7 y el uso de partes_sin_soporte; según tasks.md ambos son de T7","file":"src/server/AGENTS.md","line":10,"evidence":"AGENTS.md dice 'partes_sin_soporte aún sin uso, lo consume T6' y 'el guardrail de salida es T6'. Pero tasks.md asigna T6 a RedactorExtractivo (D12), y a T7 validacion.py (ids no recuperados, fragmentos_usados vacío, cifras) y partes_sin_soporte (S-5.1). Puede llevar al implementador de T6 a meter el guardrail en el lugar equivocado. Hay que cambiar T6 por T7 en las dos referencias."},
{"id":"F2","status":"open","severity":"medium","lens":"core","title":"consultar puede devolver Exitosa sin fuentes si el redactor no declara ids válidos (DP-2), y nada lo prueba","file":"src/server/aplicacion/consultar.py","line":9,"evidence":"Si fragmentos_usados queda vacío o todo fuera de rango, el resultado es Exitosa con fuentes=[]. Eso contradice DP-2 de standards.md ('Toda respuesta Exitosa cita al menos una fuente existente'). Hoy lo cubre el guardrail D7 dentro del redactor (T7), así que no bloquea T5. OPEN: T7 debe garantizar que ningún Redactor devuelva ids vacíos o fuera de rango, o consultar debe tener una defensa explícita. Además, el descarte de ids fuera de rango que documenta AGENTS.md no tiene prueba."},
{"id":"F3","status":"open","severity":"low","lens":"core","title":"Resultado es una dataclass congelada con un campo list mutable","file":"src/server/dominio/modelos.py","line":21,"evidence":"Resultado.fuentes es list[Fuente] dentro de una dataclass frozen=True, así que la lista se puede mutar después de crearla. Es advisory: valorar tuple[Fuente, ...] o Sequence antes de que T8 y la capa http dependan del tipo."},
{"id":"F4","status":"open","severity":"low","lens":"core","title":"El docstring de la prueba describe Estado(str, Enum); la implementación usa StrEnum","file":"tests/server/aplicacion/test_consultar.py","line":7,"evidence":"La implementación usa StrEnum (UP042), según el log de execution.md. Es advisory: ajustar el docstring para que la documentación de la API asumida no se desvíe del código."},
{"id":"F5","status":"open","severity":"low","lens":"core","title":"Warning de QdrantClient.__del__ en la suite: cierre de SQLite desde otro hilo (de T4, no de T5)","file":"tests/server/infraestructura/busqueda/test_buscador.py","line":1,"evidence":"La salida de la suite completa trae PytestUnraisableExceptionWarning: 'SQLite objects created in a thread can only be used in that same thread' en test_s31_rrf_conserva_el_orden_y_limita_a_tres_candidatos. El cliente no se cierra explícitamente en la prueba; D13 pide cerrarlo. Es advisory y pertenece a T4."}
]}
```

## T6 — attempt 1

VERDICT: PASS

## Findings (JSON)

```json
{"version":1,"findings":[{"id":"F1","status":"open","severity":"low","lens":"core","title":"OPEN: D12 says 'fragmentos que superan el umbral', but D4 only defines a threshold for the best fragment","file":"src/server/infraestructura/redactor/extractivo.py","line":10,"evidence":"D4 (design.md:61-64) only decides whether there is support by looking at the best fragment. BuscadorHibrido returns up to 3 fragments, and nothing filters each one by the threshold. RedactorExtractivo takes `fragmentos[:2]` and assumes 'El umbral ya lo aplicó el buscador' (AGENTS.md). So the second fragment may be below the threshold. Under D4 as written the code is consistent and this does not block. Advisory: confirm in D12 or D4 that the threshold applies to the query and not to each fragment, or move per-fragment filtering to the buscador (T10 calibration)."}]}
```

T6 passes. The extractive answer meets D12, and the ids are 1-based, the same convention confirmed in T5. All gates passed and the full suite gives 82 passed. The one open finding is advisory and does not block.

**What you asked me to check:**

- **D12, fixed phrase:** the answer always starts with the fixed phrase "Esto es lo que encontré en la base documental:". The tests check this.
- **D12, at most 2 fragments:** the code uses `MAXIMO_FRAGMENTOS = 2` (a named constant) and keeps the first two fragments. The test with 3 fragments confirms that `Requisitos.md` and its heading do not appear.
- **D12, `Documento > Sección` heading:** each fragment's text comes after its `Documento > Sección` heading. The test checks the order with indexes.
- **D12, never claims to cover the whole question:** the code adds no text of its own beyond the fixed phrase and the fragments, and `partes_sin_soporte` is always empty. The S-5.2/C1 test checks there is no "tasa", no "%" and no phrases claiming a full answer.
- **1-based ids:** `fragmentos_usados = range(1, len(usados)+1)` matches `consultar` (`enumerate(..., start=1)`) and the comment in `puertos.py`. With 0-based ids the S-4.1/C1 and S-5.2 assertions on `fuentes` would fail.

**Other checks:**

- **Scenarios and acceptance criteria:** S-4.1, S-4.1/C1, S-5.2 and S-5.2/C1 have unit tests that check something real. AC-3, AC-3/C1 and AC-5/C2 are covered.
- **TDD:** I have no output of the red run; relying on the Leader's account (collection failure, module missing). The only later change to the red test is the import order fix (I001), which does not weaken any assertion.
- **AGENTS.md:** has the new `redactor/extractivo.py` entry, and the T5 F1 warning is fixed (T6 changed to T7).
- **Module boundaries:** infrastructure depends only on the domain. No violations.
- **Lenses:** no risk tags, no active lens.
- **Full suite:** "82 passed, 2 warnings" (Qdrant/SQLite thread warning on GC and a Starlette deprecation), neither from this task.

**OPEN (F1):** D12 says to use the fragments "that pass the threshold", but D4 only defines a threshold for the best fragment. Under D4 as written, the implementation is consistent. Clear it up in the design or in the T10 calibration.

## T8 — attempt 1

VERDICT: FAIL

T8 falla por un solo punto, y su arreglo es pequeño. Las cuatro comprobaciones que pediste pasan: la PII no llega a ningún log, el rollback funciona cuando el INSERT falla, el SQL usa parámetros y los CHECK coinciden con data-model.md. El bloqueo viene de una de las tres decisiones: `repositorio=None` en `consultar` deja que el caso de uso devuelva una respuesta sin registrarla, y eso contradice D10, BR-6 y DP-7. La falla es del núcleo, no de seguridad.

**Lo que comprobé**

- **Spec:** S-11.1 se cumple (cinco campos más `modo`, `fecha_hora` UTC ISO 8601 con `+00:00`, fuentes registradas iguales a las devueltas). S-11.2 se cumple en el repositorio (triggers BEFORE y AFTER; `in_transaction is False` y cero filas desde otra conexión). "No registrar 413/415/422" es de T9.
- **CHECK frente a data-model.md:** coinciden (`estado`: `EXITOSA`, `SIN_INFORMACION`, `BLOQUEADA`; `modo`: `modelo`, `extractivo`, `ninguno`; `request_id` NOT NULL UNIQUE; índice sobre `fecha_hora`; `user_version = 1`).
- **SQL parametrizado:** INSERT con `?` en las siete columnas y prueba con texto de inyección. El único f-string es `PRAGMA user_version = {VERSION_ESQUEMA}`, constante entera.
- **Rollback:** `except BaseException: rollback(); raise`, con el `commit()` dentro del `try`.
- **PII:** el código nuevo no importa `logging` ni imprime nada; `test_pii_registrar_no_escribe_la_pregunta_en_los_logs` revisa `caplog` en DEBUG.
- **TDD:** hay evidencia de rojo. `redTests.changed` lista solo `test_repositorio.py` (ruff --fix I001). ASSUMPTION: no vi la versión roja original.
- **Gates:** todos en PASS; suite 110 passed y 3 warnings de `QdrantClient.__del__`, sin relación con T8.
- **Prueba inestable de T3:** coincide con esos warnings de GC/hilos de Qdrant; no bloquea T8.
- **AGENTS.md y límites de módulo:** correctos.

**Las tres decisiones**

1. **`repositorio=None` (bloquea).** D10: "el caso de uso arma el resultado y lo inserta en `consultas` ... antes de devolverlo"; DP-7 aplica. La razón dada ("no romper T5/T6") no figura como excepción en design.md. Arreglo: hacer `repositorio` obligatorio y pasar un `RepositorioDoble` (o un fixture) en las llamadas de T5/T6, sin tocar aserciones.
2. **`getattr(redactor, "modo", "modelo")` (no bloquea, arreglar junto con 1).** El Protocol ya exige `modo`. Declarar `modo` en `RedactorDoble` y usar `redactor.modo`.
3. **`fecha_hora` en UTC con precisión de segundos:** aceptable.

**Para T9 (OPEN, no bloquea T8)**

- `http/app.py` comparte una sola conexión con `check_same_thread=False`; la tabla ACID pide "una conexión por petición" y WAL. `crear_esquema` de persistencia aún no se llama al arrancar.
- El handler del 500 de T9 no debe registrar la pregunta ni `repr(resultado)`.

## Findings (JSON)

```json
{"version":1,"findings":[
{"id":"F1","status":"open","severity":"medium","lens":"core","title":"consultar puede devolver una respuesta sin registrarla (repositorio=None por defecto) en contra de D10/BR-6/DP-7","file":"src/server/aplicacion/consultar.py","line":285,"evidence":"`repositorio: RepositorioConsultas | None = None` y `if repositorio is not None:`; D10: 'El caso de uso arma el resultado y lo inserta en `consultas` en una transacción antes de devolverlo'. DP-7 aplica según el Principle check y no hay excepción justificada. Arreglo: parámetro obligatorio y pasar un doble en las llamadas de T5/T6 sin tocar aserciones."},
{"id":"F2","status":"open","severity":"low","lens":"core","title":"getattr con valor por defecto 'modelo' esconde redactores sin el atributo modo que exige el Protocol","file":"src/server/aplicacion/consultar.py","line":316,"evidence":"`return resultado, getattr(redactor, \"modo\", MODO_MODELO)`; el Protocol Redactor declara `modo: str`. Un redactor sin modo se registra como 'modelo' sin avisar. Arreglo: declarar modo en RedactorDoble y usar `redactor.modo`."},
{"id":"F3","status":"open","severity":"low","lens":"data","title":"OPEN para T9: la conexión SQLite compartida entre hilos y sin WAL contradice la tabla ACID del diseño ('una conexión por petición', WAL)","file":"src/server/http/app.py","line":27,"evidence":"`sqlite3.connect(ruta_sqlite, check_same_thread=False)` es una conexión única en lifespan; registrar() hace commit/rollback sobre ella. design.md, Data writes: 'WAL; una conexión por petición'. Además, crear_esquema de persistencia todavía no se invoca al arrancar."},
{"id":"F4","status":"open","severity":"low","lens":"core","title":"Prueba casi tautológica: tabla vacía sin llamar a consultar","file":"tests/server/infraestructura/persistencia/test_repositorio.py","line":765,"evidence":"`test_s111_c1_sin_llamar_a_consultar_no_hay_registros` solo comprueba que una tabla recién creada está vacía; la verificación real de S-11.1/C1 es la de T9. Es ruido, conviene quitarla o moverla a T9."},
{"id":"F5","status":"resolved","severity":"high","lens":"security","title":"La pregunta (PII) no llega a los logs y el SQL usa parámetros","file":"src/server/infraestructura/persistencia/repositorio.py","line":1,"evidence":"Sin logging en el código nuevo; INSERT con 7 placeholders `?`; pruebas test_pii_registrar_no_escribe_la_pregunta_en_los_logs y test_pii_el_texto_se_enlaza_como_parametro_no_se_interpola_en_el_sql."},
{"id":"F6","status":"resolved","severity":"high","lens":"data","title":"Rollback ante una falla del INSERT o del commit, sin fila parcial; los CHECK coinciden con data-model.md","file":"src/server/infraestructura/persistencia/repositorio.py","line":1,"evidence":"`try: execute; commit / except BaseException: rollback; raise`; test_falla_insert_consulta_no_deja_fila y test_falla_despues_del_insert_... comprueban in_transaction False y COUNT 0 desde otra conexión; los CHECK de estado y modo son idénticos a data-model.md."}
]}
```

## T8 — attempt 2

VERDICT: PASS

El intento 2 de T8 pasa. Los dos hallazgos que bloqueaban o había que corregir (F1 y F2) quedaron resueltos, y el retrabajo no tocó ninguna aserción existente. F3 sigue OPEN para T9, F4 sigue sin tocar y no bloquea, y hay un hallazgo nuevo de documentación, F7, de severidad baja.

**Lo que comprobé**

- **F1, resuelto:** `repositorio` es keyword-only y obligatorio. `consultar()` siempre llama a `repositorio.registrar(...)` antes de `return resultado`; si el registro falla, el error sube sin respuesta (D10, BR-6, DP-7). `test_d10_consultar_exige_repositorio` prueba ambas ramas y quedó registrada en rojo.
- **F2, resuelto:** `_resolver` devuelve `redactor.modo` directamente.
- **Retrabajo verificado en el diff:** en `test_consultar.py` las 15 llamadas solo ganan `repositorio=RepositorioDoble()` y `RedactorDoble` gana `modo = "modelo"`; en `test_extractivo.py` solo se añade un `RepositorioDoble` local en 2 llamadas. Ninguna aserción cambia; el rechazo de `run red` sobre `test_extractivo.py` es esperable.
- **TDD:** evidencia de rojo para la prueba de D10; `redTests.changed` lista solo `test_repositorio.py`, sin aserciones debilitadas. ASSUMPTION: no vi la versión roja del intento 1 de las pruebas de T8 en `test_consultar.py`.
- **Spec:** S-11.1, S-11.2 y AC-14 se siguen cumpliendo; F5 y F6 siguen resueltos. 413/415/422 queda para T9.
- **AGENTS.md, límites de módulo, gates y suite (111 passed, 3 warnings ajenos a T8):** correctos.

## Findings (JSON)

```json
{"version":1,"findings":[
{"id":"F1","status":"resolved","severity":"medium","lens":"core","title":"consultar puede devolver una respuesta sin registrarla (repositorio=None por defecto) en contra de D10/BR-6/DP-7","file":"src/server/aplicacion/consultar.py","line":285,"evidence":"Ahora `repositorio: RepositorioConsultas` es keyword-only y obligatorio, y `repositorio.registrar(...)` se ejecuta siempre antes de `return resultado`. En src/server no quedan ramas `is not None` sobre el repositorio. test_d10_consultar_exige_repositorio cubre las ramas con y sin soporte y quedó registrada en rojo."},
{"id":"F2","status":"resolved","severity":"low","lens":"core","title":"getattr con valor por defecto 'modelo' esconde redactores sin el atributo modo que exige el Protocol","file":"src/server/aplicacion/consultar.py","line":319,"evidence":"`return resultado, redactor.modo`; en src/server ya no hay getattr. RedactorDoble declara `modo = \"modelo\"` y RedactorExtractivo `modo = \"extractivo\"`."},
{"id":"F3","status":"open","severity":"low","lens":"data","title":"OPEN para T9: la conexión SQLite compartida entre hilos y sin WAL contradice la tabla ACID del diseño ('una conexión por petición', WAL)","file":"src/server/http/app.py","line":27,"evidence":"Sin cambios en este intento: `sqlite3.connect(ruta_sqlite, check_same_thread=False)` es una conexión única en lifespan y crear_esquema de persistencia todavía no se invoca al arrancar. Queda para T9."},
{"id":"F4","status":"open","severity":"low","lens":"core","title":"Prueba casi tautológica: tabla vacía sin llamar a consultar","file":"tests/server/infraestructura/persistencia/test_repositorio.py","line":977,"evidence":"`test_s111_c1_sin_llamar_a_consultar_no_hay_registros` solo comprueba que una tabla recién creada está vacía; la verificación real de S-11.1/C1 (413/415/422 sin registro) es de T9. No bloquea."},
{"id":"F5","status":"resolved","severity":"high","lens":"security","title":"La pregunta (PII) no llega a los logs y el SQL usa parámetros","file":"src/server/infraestructura/persistencia/repositorio.py","line":1,"evidence":"Sin cambios desde el intento 1: no hay logging en el código nuevo, el INSERT usa 7 placeholders `?` y siguen test_pii_registrar_no_escribe_la_pregunta_en_los_logs y test_pii_el_texto_se_enlaza_como_parametro_no_se_interpola_en_el_sql."},
{"id":"F6","status":"resolved","severity":"high","lens":"data","title":"Rollback ante una falla del INSERT o del commit, sin fila parcial; los CHECK coinciden con data-model.md","file":"src/server/infraestructura/persistencia/repositorio.py","line":1,"evidence":"Sin cambios desde el intento 1: `try: execute; commit / except BaseException: rollback; raise`; test_falla_insert_consulta_no_deja_fila y test_falla_despues_del_insert_hace_rollback_y_no_deja_fila_incompleta siguen en PASS."},
{"id":"F7","status":"open","severity":"low","lens":"core","title":"El docstring de test_repositorio.py describe la API anterior (repositorio=None opcional)","file":"tests/server/infraestructura/persistencia/test_repositorio.py","line":758,"evidence":"`consultar(pregunta, *, buscador, redactor, repositorio=None, request_id=None)` y '`repositorio` es opcional para no romper las pruebas de T5/T6' contradicen la implementación corregida en F1 y src/server/AGENTS.md. Es solo documentación; conviene actualizar el texto."}
]}
```
