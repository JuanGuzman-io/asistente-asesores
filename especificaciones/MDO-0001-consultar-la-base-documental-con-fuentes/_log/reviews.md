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

## T7 — attempt 1

VERDICT: PASS

## Resumen

T7 cumple su "Done when" (tasks.md:280-285) y las cláusulas de D7 y D9. Ningún hallazgo bloquea. Dejo cinco avisos. Uno de severidad media debe resolverse en T9: `modo` es estado compartido y puede quedar mal registrado con peticiones concurrentes.

## Comprobaciones pedidas

**Pruebas rojas.** Fallaron con exit 2 en la recolección porque faltaban los módulos; rojo legítimo. Los 20 nombres de `test_validacion.py` y los 23 de `test_gemini.py` registrados en `state.yml:192-240` coinciden con los actuales; no se eliminó ningún caso. ASSUMPTION: el único cambio es I001 (sin shell ni versión roja para diff byte a byte); las aserciones siguen siendo estrictas.

**Guardrail D7** (`validacion.py`): ids exigidos en `1..len(fragmentos)` (cubiertos 0, -1, len+1, 99 y sin fragmentos); cifras como tokens completos (`\d+(?:[.,]\d+)*%?`) solo contra los fragmentos citados, también en `partes_sin_soporte`; la frase "No encontré información sobre …" la arma el código, en orden y al final.

**`fragmentos_usados` vacío (cambio en `consultar.py`).** D7 dice a la vez "se descarta si está vacío" y "si el modelo declara que ninguna parte tiene soporte → `Sin información suficiente`". Sin partes declaradas, se descarta y se usa el extractivo; con partes declaradas, `consultar` devuelve `MENSAJE_SIN_INFORMACION` sin fuentes. En ningún camino se entrega texto del modelo sin respaldo. Hace falta dejar esta lectura escrita en D7 (F1).

**`contents`.** Fragmentos y pregunta solo en `contents`, en `<fragmento id="N">` y `<pregunta>`; etiquetas neutralizadas sin distinguir mayúsculas, con espacios y `/`. `system_instruction` es `prompt.md` íntegro. Pruebas de inyección en dos variantes. El D5 real trata de FTS; la regla es D7/DP-1 (F5).

**Clave.** `__repr__` solo muestra `con_clave=bool`; los logs solo llevan `type(error).__name__`; `SalidaInvalida ... from None` corta el `ValidationError`; las pruebas meten clave y pregunta en el mensaje de error del cliente y de la fábrica.

**Respaldo extractivo.** Probado en todos los fallos (sin clave, API, timeout, fábrica, JSON inválido, esquema incompleto, tipos incorrectos, `SalidaInvalida`), un solo intento con `HttpOptions(timeout=5000)`. Se registra un warning; D9 lo manda.

**Prompt v1.** Coherente con D7. Aviso: `model-registry.md:51` dice "(por crear)" (F4).

**Import diferido.** Justificado y documentado en `AGENTS.md`.

**Dependencia y MIT-0.** `google-genai==2.33.0` fijada, nombrada en `architecture.md` y `standards.md`. MIT-0 es permisiva; no bloquea.

**Hilos y T9** (F2). Con ruta `def` síncrona en threadpool y una sola instancia de `RedactorGemini`, una petición puede leer el `modo` de otra y `consultar` registraría un `modo` equivocado (D10). Opciones: `modo` en `RespuestaRedactada` o un redactor por petición. No bloquea T7; T9 debe resolverlo.

**Gates.** Todos PASS; suite completa `170 passed, 2 warnings` (GC conocido de `QdrantClient`). `AGENTS.md` refleja los módulos nuevos y el cambio en `consultar.py`.

## Findings (JSON)

```json
{"version":1,"findings":[
{"id":"F1","status":"open","severity":"low","lens":"ai","title":"La lectura de D7 sobre 'fragmentos_usados vacío' no está escrita en design.md","file":"especificaciones/MDO-0001-consultar-la-base-documental-con-fuentes/design.md","line":96,"evidence":"D7 dice que se descarta si fragmentos_usados está vacío y, a la vez, que una declaración de 'ninguna parte con soporte' da Sin información suficiente. El código descarta un [] sin partes y trata [] con partes como esa declaración (validacion.py:32, consultar.py:39-42). Es coherente y no entrega texto del modelo, pero es un ASSUMPTION del tester: conviene registrarlo en D7."},
{"id":"F2","status":"open","severity":"medium","lens":"data","title":"`modo` es estado de instancia compartido: puede registrar un modo equivocado con peticiones concurrentes (T9)","file":"src/server/infraestructura/redactor/gemini.py","line":84,"evidence":"redactar() asigna self.modo y consultar lo lee después (consultar.py:42,46). Una ruta `def` de FastAPI corre en un threadpool, así que entre la escritura y la lectura puede colarse otra petición y el registro D10 quedaría con un modo erróneo. Hay que resolverlo en T9: modo en RespuestaRedactada o un redactor por petición."},
{"id":"F3","status":"open","severity":"medium","lens":"ai","title":"S-5.1 y S-4.2/C1 son de nivel eval, pero ninguna tarea evalúa el modelo real","file":"especificaciones/MDO-0001-consultar-la-base-documental-con-fuentes/tasks.md","line":295,"evidence":"test_levels marca S-4.2/C1 y S-5.1 como eval. T7 solo usa dobles, como pide standards.md:39, y las evals de T10 corren 'en modo extractivo' (tasks.md:375). OPEN para el Leader o el PE: no hay medición del comportamiento real de Gemini ante datos inventados no numéricos, que el guardrail de cifras no detecta."},
{"id":"F4","status":"open","severity":"low","lens":"ai","title":"model-registry.md todavía marca el prompt como '(por crear)'","file":"constitucion/model-registry.md","line":51,"evidence":"prompt.md v1 ya existe y AGENTS.md exige mantener model-registry.md al día. Habría que quitar '(por crear)' de la fila del prompt."},
{"id":"F5","status":"open","severity":"low","lens":"core","title":"Las pruebas de inyección se nombran D5, pero D5 es la decisión de FTS","file":"tests/server/infraestructura/redactor/test_gemini.py","line":389,"evidence":"design.md:74 define D5 como 'La pregunta es datos en la búsqueda' (FTS). La regla que verifican estas pruebas es D7/DP-1. Sería un renombrado en la siguiente tarea que toque el archivo; no bloquea."},
{"id":"F6","status":"resolved","severity":"low","lens":"core","title":"Pruebas rojas modificadas por ruff I001","file":"tests/server/infraestructura/redactor/test_gemini.py","line":44,"evidence":"Los 43 nombres de prueba registrados en rojo (state.yml:192-240) siguen presentes y no se eliminó ningún caso. No hubo diff byte a byte (ASSUMPTION): imports ordenados y aserciones estrictas sin señales de debilitamiento."},
{"id":"F7","status":"resolved","severity":"low","lens":"security","title":"Licencia MIT-0 de la transitiva cffi","file":"uv.lock","line":1,"evidence":"standards.md:62 permite 'solo licencias permisivas'. MIT-0 es permisiva (MIT sin la cláusula de atribución). No hace falta una decisión nueva del PE; se recomienda añadirla a la excepción ya aprobada para trazabilidad."}
]}
```

## T9 — attempt 1

VERDICT: PASS

## Resumen

Revisé T9 con el paquete `.mandao/cache/MDO-0001/reviews/T9-1-pack.md` y los gates de `.mandao/cache/MDO-0001/gates/T9-1.md`. Los lentes activos son core, security y data. Ninguno de mis hallazgos bloquea; todos son consultivos.

**Pruebas.** El gate de pruebas de T9 da 41 passed. `T9-1-fullsuite.txt` muestra una sola corrida: 211 passed, 2 warnings. Las otras dos corridas mencionadas no están en ese archivo, así que no las puedo verificar.

**Spec y contrato:**
- **S-7.1, S-7.2, C1 y C2:** se cumplen. NFC, `strip()`, 1 a 1.000 puntos de código; una pregunta rechazada no se recorta, no se busca y no se registra.
- **S-9.1:** se cumple. 413 por `Content-Length` y también chunked (el middleware cuenta los bytes); 16.384 bytes exactos pasan el middleware y dan 422.
- **S-9.2:** se cumple. 415 con `text/plain`, otros tipos y sin `Content-Type`; acepta JSON con `charset` y en mayúsculas.
- **S-14.1 y AC-3:** se cumplen. Exactamente `respuesta`, `fuentes` y `estado`, y `X-Request-Id`.
- **S-11.1/C1 y AC-14/C1:** se cumplen. 413, 415 y 422 no dejan filas.
- **RFC 9457:** se cumple, también en 404, 405 y 500.
- **`detail` del 422:** solo `loc` y `msg`; ninguna prueba lo protege (F7).
- **La pregunta en logs:** `registrar_peticion` nunca la recibe; el 500 registra solo el tipo de la excepción.

**Pendientes de revisiones anteriores:** cerrados (F1 a F5).

**Evidencia de rojo.** Formalmente cumple; todas fallaron por el `TypeError` del kwarg. Revisé cada aserción fina de forma independiente: WAL, conexión por petición, log JSON y 500 sin PII discriminan. La concurrente de `modo` solo discrimina si las peticiones se solapan de verdad; pido evidencia de mutación (F6).

**`RedactorExclusivo` frente al p95 de 3 s.** Aceptable para esta entrega (ejecución local de un usuario, NFR-1 con locust, T9 sin tag `perf`), pero bajo carga concurrente con Gemini la espera se acumula hasta N×5 s. Deuda (F8).

**Clave y entrypoint.** Leer la clave de `os.environ` cumple security.md. `AGENTS.md` documenta un comando de arranque incompleto y no existe una `app` a nivel de módulo (F10).

## Findings (JSON)

```json
{"version":1,"findings":[
{"id":"F1","status":"resolved","severity":"high","lens":"data","title":"Conexión SQLite por petición y WAL (F3 de T8)","file":"src/server/http/rutas.py","line":40,"evidence":"Cada petición abre su conexión con closing(sqlite3.connect(ruta_sqlite)) en su hilo, sin check_same_thread=False. El lifespan activa PRAGMA journal_mode=WAL. Lo protegen test_acid_cada_peticion_abre_su_propia_conexion_sqlite_y_la_cierra y test_el_arranque_crea_la_tabla_consultas_vacia_con_wal."},
{"id":"F2","status":"resolved","severity":"medium","lens":"data","title":"crear_esquema de consultas al arrancar","file":"src/server/http/app.py","line":43,"evidence":"El lifespan llama a crear_esquema(conexion) antes de indexar. La prueba comprueba la tabla, user_version 1 y que empieza vacía."},
{"id":"F3","status":"resolved","severity":"high","lens":"data","title":"modo seguro entre hilos (F2 de T7)","file":"src/server/http/rutas.py","line":19,"evidence":"RedactorExclusivo serializa redactar y copia modo bajo el candado a una instancia por petición. consultar solo lee redactor.modo después de redactar, así que el valor inicial leído sin candado nunca se registra."},
{"id":"F4","status":"resolved","severity":"high","lens":"security","title":"413, 415 y 422 sin registro","file":"src/server/http/middleware.py","line":45,"evidence":"415 y 413 se responden en el middleware antes de llegar a la app, y el 422 ocurre antes del caso de uso. Lo cubren test_s11_1_c1_tras_413_415_y_422..., _sin_efectos en cada caso y la vía chunked."},
{"id":"F5","status":"resolved","severity":"high","lens":"security","title":"El 500 no lleva la pregunta ni el mensaje de la excepción","file":"src/server/http/middleware.py","line":30,"evidence":"Se captura Exception, se responde con DETALLES[500] y solo se registra type(error).__name__. Además la excepción no se re-lanza al servidor, que de otro modo registraría la traza con PII."},
{"id":"F6","status":"open","severity":"medium","lens":"core","title":"Falta evidencia de mutación para la prueba concurrente de modo","file":"tests/server/http/test_consultar_api.py","line":306,"evidence":"El rojo falló por TypeError en crear_app, no por la carrera. Si las dos peticiones no se solapan, cada wait(1.0) vence y la prueba pasa aunque no haya aislamiento: ninguna aserción comprueba que hubo solapamiento. ASSUMPTION: el TestClient comparte el portal y despacha concurrentemente al threadpool. OPEN: registrar la mutación (pasar app.state.redactor sin envolver) y verla fallar, o afirmar el solapamiento en la prueba."},
{"id":"F7","status":"open","severity":"medium","lens":"security","title":"Ninguna prueba garantiza que el detail del 422 no refleje la entrada","file":"tests/server/http/test_consultar_api.py","line":394,"evidence":"La implementación es correcta: manejar_validacion usa solo loc y msg. Pero test_nfr4_una_peticion_rechazada... solo revisa caplog y no comprueba que SECRETO esté ausente de respuesta.text. FastAPI por defecto incluye 'input' en el 422, así que volver al handler por defecto no rompería ninguna prueba. Consultivo: ninguna regla escrita exige esto en la respuesta, solo en los logs."},
{"id":"F8","status":"open","severity":"medium","lens":"performance","title":"El candado serializa las llamadas a Gemini (hasta 5 s cada una)","file":"src/server/http/rutas.py","line":32,"evidence":"Con N peticiones concurrentes con modelo, la última espera hasta N×5 s, en conflicto con NFR-1 y performance.md (p95 ≤ 3 s) bajo la prueba de carga. Aceptable hoy por la ejecución local de un usuario (security.md) y porque T9 no tiene el tag perf. Alternativa sin candado: que RespuestaRedactada devuelva el modo (cambio de puerto). Debe resolverse o medirse antes de T10/NFR-1."},
{"id":"F9","status":"open","severity":"low","lens":"core","title":"El 500 vive en el middleware y no en un handler de Exception como dice D8; T12 apunta a otros archivos","file":"src/server/http/middleware.py","line":30,"evidence":"D8 pide un handler de Exception. El middleware es la mejor opción, porque ServerErrorMiddleware re-lanza la excepción al servidor y este registraría la traza con PII. Aun así conviene anotar la desviación en design.md o en el plan de T12, que lista problemas.py y app.py."},
{"id":"F10","status":"open","severity":"low","lens":"core","title":"Entrypoint de uvicorn documentado como placeholder","file":"src/server/AGENTS.md","line":21,"evidence":"AGENTS.md dice 'uvicorn src.server.http.app:...' y no existe una app a nivel de módulo ni una fábrica nombrada. OPEN: que una tarea posterior (README o arranque) la cree y AGENTS.md la nombre."},
{"id":"F11","status":"open","severity":"low","lens":"core","title":"ConsultaSalida.estado es str y no el enum del contrato","file":"src/server/http/esquemas.py","line":33,"evidence":"El contrato de design.md fija 'Exitosa' | 'Sin información suficiente' | 'Bloqueada por seguridad'. Con str, OpenAPI no lo expresa ante MDO-0003. Sugerencia: Literal o Estado."},
{"id":"F12","status":"open","severity":"low","lens":"core","title":"El 405 pierde la cabecera Allow","file":"src/server/http/problemas.py","line":47,"evidence":"manejar_http no copia exc.headers, y RFC 9110 exige Allow en un 405."},
{"id":"F13","status":"open","severity":"low","lens":"security","title":"Un Content-Length no numérico responde 413 y no 400","file":"src/server/http/middleware.py","line":89,"evidence":"Se rechaza igual (falla cerrado), pero con un código engañoso. El servidor real suele rechazarlo antes."},
{"id":"F14","status":"open","severity":"low","lens":"core","title":"conftest.py fuera de la lista de archivos y type: ignore obsoleto","file":"tests/server/http/conftest.py","line":107,"evidence":"conftest.py no está en files de T9, aunque es infraestructura de prueba razonable. El ignore[call-arg] quedó sobrando porque redactor ya existe en crear_app, y mypy solo revisa src, así que no lo detecta."},
{"id":"F15","status":"open","severity":"low","lens":"core","title":"El logger asistente.http tiene handler propio y también propaga","file":"src/server/http/logs.py","line":8,"evidence":"Si uvicorn o la raíz configuran un handler, cada línea JSON sale dos veces."}
]}
```

## T10 — attempt 1

VERDICT: FAIL

## Resumen

T10 no se puede aceptar todavía. Las evals cumplen los objetivos y los números de D4 coinciden con los que midió el implementador, pero hay tres hallazgos que bloquean:

- **F1:** la clave del caché de embeddings no cubre lo que ahora se embebe.
- **F2:** las evals descargan el modelo dentro del gate por defecto, contra `standards.md:39`.
- **F3:** el gate `secrets` falla, aunque el contexto decía "los demás gates pasan".

## Verificación de lo pedido

**Los números de D4 coinciden** con la salida del implementador (T10-fullsuite.txt y T10-impacted.txt): EV-1 0,955, EV-2 1,000, EV-3 0,000, EV-4 1,000 y EV-5 1,000; coseno con soporte 0,556–0,667–0,881 y sin soporte 0,095–0,412–0,599; la sin soporte más alta con FTS es s06 (0,517) y la con soporte más baja es c09 (0,556). Ambas salidas dicen 59 y 228 passed.

**Las evals miden la tabla EV de `requirements.md`:** EV-1 y EV-3 sobre con_respuesta y parcial (22), EV-2 sobre sin_respuesta y fuera_de_tema (10), EV-4 y EV-5 sobre las `Exitosa`. EV-6 queda fuera con justificación. EV-4 en modo extractivo se cumple casi por construcción, pero así lo define la tabla.

**Sobreajuste.** El contenido del dataset no depende del umbral, pero el umbral se eligió mirando ese mismo dataset: los EV son resultados dentro de la muestra. C-5 lo permite; advertencia en F4.

**Margen de 0,54:** el punto medio entre 0,517 y 0,556 es 0,5365, así que 0,54 es correcto. D4 omite márgenes más estrechos: s02 mide 0,599 contra `UMBRAL_ALTO` 0,60 (0,001), y s05 mide 0,531, 0,009 bajo `UMBRAL_BAJO`, fuera solo porque no coincide en FTS. Con 10 preguntas en EV-2, un solo cambio baja EV-2 a 0,90 (F4).

**D11, segundo arranque sin recalcular.** `test_cambiar_la_version_del_formato_recrea_la_coleccion` comprueba ambos lados. El problema está en la clave del caché (F1).

**El e2e cubre cada punto del "Done when"** (S-4.1; token interno y clave temporal; S-10.1; S-11.1 con 415, 413, 422 y 422 sin fila; S-5.2). **Primera corrida en verde del e2e:** revisé las aserciones de forma independiente; comparan valores concretos sobre el pipeline real y solo el embedding es un doble. Basta como evidencia del flujo.

**Nada se debilitó en las pruebas:** en `test_indice.py` y `test_buscador.py` solo cambia la clave de los dobles; 0,50 → 0,56 mantiene ambos casos entre umbrales; sigue la prueba con 0,35; el renombre a `..._calibrados_...` está justificado y el rojo está registrado (`execution.md` líneas 76–80).

**El confidencial no llega al dataset ni a los registros:** s04 y s05 solo contienen la pregunta; el e2e lee el confidencial al ejecutarse sin copiarlo; el reporte de las evals imprime solo id, coseno, estado y pregunta; `indice.py` registra solo conteos.

## Findings (JSON)

```json
{"version":1,"findings":[
{"id":"F1","status":"open","severity":"medium","lens":"data","title":"La clave del caché de embeddings (hash de `texto`) no cubre documento ni sección, que ahora se embeben: al renombrar quedan vectores viejos","file":"src/server/infraestructura/busqueda/indice.py","line":112,"evidence":"`con_hash = [(f, hash_normalizado(f.texto)) ...]`; `nuevos = {h: texto_indexable(f) for f, h in con_hash if h not in existentes}`. Si cambia `documento` o `seccion` con el mismo texto, el hash ya existe y no se vuelve a embeber; FTS sí se reconstruye. Incumple D4 ('lo que se embebe es documento > sección\\ntexto')."},
{"id":"F2","status":"open","severity":"medium","lens":"performance","title":"Las evals descargan el modelo real dentro del gate de test por defecto, contra standards.md:39, sin excepción registrada","file":"pyproject.toml","line":23,"evidence":"Se registra el marker `eval` pero no hay `addopts = -m 'not eval'`; `uv run pytest` ejecuta tests/server/evals con `EmbeddingsFastembed` (0,22 GB). standards.md:39: 'Las pruebas nunca llaman a Gemini ni descargan modelos'. La excepción solo está en el docstring y no se descartó la alternativa más simple (excluir por defecto y correrlas en `verify`)."},
{"id":"F3","status":"open","severity":"medium","lens":"core","title":"El gate secrets falla (falso positivo en una prueba de T9) y el contexto lo daba por aprobado","file":"tests/server/http/test_consultar_api.py","line":323,"evidence":"gates/T10-1.md: secrets FAIL exit 1, 'Secret Keyword' en `SECRETO = \"cliente-Zeta-4821\"`. Marcar con `pragma: allowlist secret` o actualizar .secrets.baseline."},
{"id":"F4","status":"open","severity":"medium","lens":"performance","title":"D4 declara un margen de ≈0,02 pero omite márgenes de 0,001 (UMBRAL_ALTO) y 0,009 (UMBRAL_BAJO); la calibración es dentro de la muestra","file":"especificaciones/MDO-0001-consultar-la-base-documental-con-fuentes/design.md","line":74,"evidence":"T10-fullsuite.txt: s02 0,599 frente a 0,60 (no hay umbral más alto que lo salve); s05 0,531, 0,009 bajo 0,54, solo queda fuera porque no coincide en FTS. EV-2 tiene n=10: un solo cambio la deja en 0,90. Los umbrales se eligieron con el mismo consultas@v1 que mide los EV."},
{"id":"F5","status":"open","severity":"low","lens":"data","title":"FTS5 de contenido externo indexa un texto distinto de la tabla de contenido, y la sección se indexa dos veces","file":"src/server/infraestructura/busqueda/indice.py","line":90,"evidence":"esquema.py: `content='fragmentos'`; se inserta `texto_indexable(fragmento)` en la columna `texto` mientras `fragmentos.texto` guarda el cuerpo. 'rebuild', 'delete' por fila, snippet o integrity-check quedarían inconsistentes; `seccion` aparece en su columna y dentro de `texto` (peso BM25)."},
{"id":"F6","status":"open","severity":"low","lens":"core","title":"La aserción 'no afirma cubrir toda la pregunta' de S-5.2 prueba poco, y el oráculo copia el formato de texto_indexable en literal","file":"tests/server/e2e/test_flujo_consulta.py","line":1021,"evidence":"`assert \"No encontré información sobre\" not in ...` no demuestra la cláusula; C-1 lo cubre el `startswith(ENCABEZADO_EXTRACTIVO)`. `EmbeddingsOraculo` reconstruye la clave `f\"{documento} > {seccion}\\n{texto}\"` a mano."},
{"id":"F7","status":"resolved","severity":"low","lens":"core","title":"Gate de test con exit 4 por problema de la herramienta (isTestFile trata consultas.json como prueba)","file":"tests/fixtures/consultas.json","line":1,"evidence":"gates/T10-1.md: 'ERROR: not found ... consultas.json'. Evidencia alternativa del Leader: T10-impacted.txt 59 passed, T10-fullsuite.txt 228 passed, con los EV impresos."}
]}
```

## T10 — attempt 2

VERDICT: PASS

## Resumen

T10, intento 2: F1 a F6 quedan resueltos, D11 se mantiene y ninguna aserción se debilitó. Doy PASS. Hay una condición antes de cerrar la tarea (F8): el paquete no trae la salida de la suite sin evals. El "223 passed" lo informa el Leader y no está en `gates/T10-2.md`, así que no lo doy por verificado.

## Verificación

**F1, resuelto.** En `indice.py`, la clave del caché es `clave_embedding(f) = hash_normalizado(texto_indexable(f))`, el id del punto es el UUID v5 de esa clave y el payload es `{hash, clave}`. `_claves_en_qdrant` lee `clave` y los obsoletos son `existentes - claves.keys()`: al renombrar un documento o una sección se vuelve a embeber y el punto viejo se borra después del commit. `payload.hash` y `fragmentos.hash` siguen siendo el hash de `texto`. `VERSION_FORMATO = "v3-clave-texto-indexable"` recrea las colecciones anteriores. La prueba roja `test_renombrar_la_seccion_con_el_mismo_texto_vuelve_a_embeber` cubre sección y documento; su rojo está en `execution.md:83`.

**F2, resuelto.** `pyproject.toml` tiene `addopts = "-m 'not eval'"` y `.mandao/config.yml:23` define `metrics: uv run pytest -m eval`. La salida del gate confirma "collected 230 items / 223 deselected / 7 selected" y "7 passed", con EV-1 0,955, EV-2 1,000, EV-3 0,000, EV-4 1,000 y EV-5 1,000. La excepción a `standards.md:39` está justificada en D4 como decisión del PE, y el README la documenta.

**F3, resuelto.** `# pragma: allowlist secret` en `test_consultar_api.py:323`; gate `secrets` PASS.

**F4, resuelto.** D4 declara los márgenes de 0,001 (s02) y 0,009 (s05), n=10 en EV-2 y que la calibración es dentro de la muestra. Pendiente de commit de docs aparte.

**F5, resuelto.** `src/server/AGENTS.md` documenta que FTS5 de contenido externo indexa `texto_indexable` y advierte sobre `rebuild`, `delete` por fila, `snippet` e `integrity-check`.

**F6, resuelto en lo que bloqueaba.** El oráculo importa `texto_indexable`. La aserción débil sigue, pero C-1 lo cubre `startswith(ENCABEZADO_EXTRACTIVO)`.

**D11 se mantiene.** `test_segundo_arranque_sin_cambios_calcula_cero_embeddings` sigue afirmando `segundo.textos == []`; `test_cambiar_la_version_del_formato_recrea_la_coleccion` comprueba ambos lados.

**No se debilitó ninguna aserción.** Solo cambian claves de dobles; 0,50 → 0,56 sigue entre umbrales; el renombre `..._calibrados_...` mantiene la aserción con motivo registrado; en el e2e solo cambia el doble.

**Gates.** format, lint, typecheck, secrets, audit, sast y metrics PASS. `test` FAIL con exit 4 por el defecto de la herramienta (`isTestFile` pasa `consultas.json` a pytest), no del código.

## Findings (JSON)

```json
{"version":1,"findings":[
{"id":"F1","status":"resolved","severity":"medium","lens":"data","title":"La clave del caché de embeddings ahora es el hash de texto_indexable","file":"src/server/infraestructura/busqueda/indice.py","line":430,"evidence":"`clave_embedding(f) = hash_normalizado(texto_indexable(f))`; id = UUID v5 de la clave; payload `{hash, clave}`; `obsoletos = existentes - claves.keys()`; VERSION_FORMATO v3. Prueba roja parametrizada (sección y documento) registrada en execution.md:83."},
{"id":"F2","status":"resolved","severity":"medium","lens":"performance","title":"Las evals salen del gate por defecto y pasan al gate metrics","file":"pyproject.toml","line":23,"evidence":"`addopts = \"-m 'not eval'\"`; `.mandao/config.yml:23` `metrics: uv run pytest -m eval`; salida: '230 items / 223 deselected / 7 selected', '7 passed'. La excepción a standards.md:39 está justificada en D4 (PE 2026-10-23)."},
{"id":"F3","status":"resolved","severity":"medium","lens":"core","title":"Falso positivo del gate secrets marcado con pragma","file":"tests/server/http/test_consultar_api.py","line":323,"evidence":"`SECRETO = \"cliente-Zeta-4821\"  # pragma: allowlist secret`; gate secrets PASS, exit 0."},
{"id":"F4","status":"resolved","severity":"medium","lens":"performance","title":"D4 declara los márgenes reales y que la calibración es dentro de la muestra","file":"especificaciones/MDO-0001-consultar-la-base-documental-con-fuentes/design.md","line":74,"evidence":"D4: '0,001 bajo UMBRAL_ALTO (s02, 0,599...)', '0,009 bajo UMBRAL_BAJO (s05, 0,531...)', 'EV-2 tiene n = 10', 'La calibración es dentro de la muestra'. Pendiente de commit de docs, según el Leader."},
{"id":"F5","status":"resolved","severity":"low","lens":"data","title":"AGENTS.md documenta que FTS5 de contenido externo indexa texto_indexable","file":"src/server/AGENTS.md","line":17,"evidence":"'fragmentos_fts (FTS5 de contenido externo) indexa texto_indexable... no usar rebuild, delete por fila, snippet ni integrity-check sin revisar este punto'. Sugerencia sin bloqueo: seccion sigue pesando dos veces en BM25."},
{"id":"F6","status":"resolved","severity":"low","lens":"core","title":"El oráculo del e2e importa texto_indexable","file":"tests/server/e2e/test_flujo_consulta.py","line":900,"evidence":"`from src.server.infraestructura.busqueda.indice import texto_indexable`. Sugerencia sin bloqueo: la aserción `\"No encontré información sobre\" not in` sigue siendo débil; C-1 lo cubre `startswith(ENCABEZADO_EXTRACTIVO)`."},
{"id":"F7","status":"resolved","severity":"low","lens":"core","title":"El gate test da exit 4 por el defecto de la herramienta (isTestFile pasa consultas.json a pytest)","file":"tests/fixtures/consultas.json","line":1,"evidence":"gates/T10-2.md: 'ERROR: not found: .../tests/fixtures/consultas.json', 'collected 0 items'. No es un defecto del código."},
{"id":"F8","status":"open","severity":"medium","lens":"core","title":"No hay salida de la suite sin evals en este intento: '223 passed' lo informa el Leader y no está en el paquete","file":".mandao/cache/MDO-0001/gates/T10-2.md","line":38,"evidence":"El gate test falló antes de ejecutar pruebas y el paquete no incluye la salida de `uv run pytest -q`. Lo único verificable son los 223 deseleccionados del gate metrics. OPEN: adjuntar la salida tal como se ejecutó (p. ej. un T10-2-fullsuite.txt) antes de marcar T10 como hecha."},
{"id":"F9","status":"open","severity":"low","lens":"data","title":"_claves_en_qdrant lanza KeyError si un punto no tiene payload 'clave'","file":"src/server/infraestructura/busqueda/indice.py","line":466,"evidence":"`str(p.payload[\"clave\"]) for p in puntos if p.payload`. En producción, VERSION_FORMATO recrea las colecciones anteriores; un punto insertado a mano solo con `hash` (como los huérfanos de test_buscador) rompería un reindexado posterior. Sugerencia: `.get(\"clave\")` y tratarlo como obsoleto."}
]}
```

## T11 — test review 1 (via claude)

TEST REVIEW: PASS

Esta conclusión sale solo de leer el código. No ejecuté nada y no tengo la salida de las pruebas, así que no afirmo que pasen. Lo que sí confirmé leyendo es que las tres mutaciones que el tester dice haber probado las matan las pruebas indicadas, con exactamente el número de fallos que declara (2, 2 y 7).

## Assertions

### tests/server/aplicacion/test_respaldo.py (18 casos)

- **`test_s12_1_con_el_cliente_lanzando_error_...` (9 casos parametrizados).** Mata capturar solo `(RuntimeError, OSError, ValueError)` en `gemini.py:79`: `APIError` hereda de `Exception` (`google/genai/errors.py:56`), `ServerError` y `ClientError` de `APIError`, y los timeouts de `httpx` de `TransportError → RequestError → HTTPError → Exception`, no de `OSError`. Fallarían 6 casos más el secuencial: 7. También mata reintentos (`cliente.llamadas == 1`), quitar el `except` genérico y un respaldo con otro formato (`ENCABEZADO`, orden de fuentes, `modo == "extractivo"`).
- **`test_s12_1_con_el_cliente_que_agota_el_tiempo_...`.** Mata quitar el `except` y añadir reintentos; no el `except` estrecho (`TimeoutError` es `OSError`).
- **`test_s12_1_el_modo_registrado_sigue_a_cada_consulta_modelo_y_luego_extractivo`.** Mata quitar `self.modo = MODO_EXTRACTIVO` (`gemini.py:109`) → `["modelo","modelo"]`; leer `redactor.modo` antes de `redactar` → `["extractivo", ...]`; y el `except` estrecho (`ServerError` se propaga).
- **`test_s12_1_si_la_fabrica_del_cliente_falla_...`.** Mata crear el cliente fuera del `try` y propagar el error de la fábrica.
- **`test_s12_1_el_error_del_cliente_no_se_propaga_ni_filtra_...`.** Mata registrar `str(error)` en lugar de `type(error).__name__` (`gemini.py:82`).
- **`test_s12_2_sin_clave_no_se_llama_a_la_fabrica_...` (`None`, `""`).** Mata quitar la guarda `if not self._api_key` (`gemini.py:73`) y cambiarla a `is None`.
- **`test_s12_2_sin_clave_la_fabrica_por_defecto_no_crea_genai_client`.** Mata la misma guarda con la fábrica real.
- **`test_d9_la_fabrica_por_defecto_usa_httpoptions_timeout_5000_...`.** Mata cambiar `TIMEOUT_MS`, quitar `http_options` y añadir `retry_options`.
- **`test_d9_el_cliente_real_creado_por_la_fabrica_...`.** Mata las mismas mutaciones sobre el cliente real; depende de atributos privados (F5).

### tests/server/e2e/test_respaldo_e2e.py (5 casos)

- **`test_s12_1_con_gemini_caido_responde_200_extractiva_...` (error y tiempo agotado).** Mata la propagación hasta el middleware (500), un respaldo sin fuentes, otro `modo`, otra respuesta o `request_id`, y los reintentos.
- **`test_s12_1_dos_consultas_con_gemini_caido_...`.** Caída sostenida registrada como `extractivo` dos veces; débil frente a mutaciones (F6).
- **`test_s12_2_crear_app_sin_gemini_api_key_...`.** Mata leer la clave de otra fuente o crear el cliente sin clave.
- **`test_s12_1_modelo_y_luego_gemini_caido_registra_modelo_y_luego_extractivo`.** Mata quitar `self.modo = MODO_EXTRACTIVO` y, en `RedactorExclusivo` (`rutas.py:29-34`), quitar la copia de `modo` tras `redactar` o hacerla antes.

### Nota del Leader sobre una entrada inválida

La entrada `tests/server/aplicacion/test_respaldo.py tests/server/e2e/test_respaldo_e2e.py` (las dos rutas en un solo argumento) viene de un `run red` mal entrecomillado del tester: pytest salió con exit 4 y 0 pruebas recogidas. Esa fila RED de `execution.md` no es evidencia de rojo. Los dos archivos reales son los inspeccionados arriba y pasaron en su primera ejecución.

### Cobertura de la Definition of Done de T11
S-12.1 (E2E), S-12.2 (unitaria y E2E), `HttpOptions(timeout=5000)` sin `retry_options` (dos pruebas D9) y E2E con registro: cubiertos. Sin casos sobrantes ni eliminados.

## Findings (JSON)

```json
{"version":1,"findings":[
{"id":"F1","status":"resolved","severity":"high","lens":"ai","title":"Ninguna prueba detectaba un modo 'modelo' rancio tras un éxito seguido de una caída","file":"tests/server/aplicacion/test_respaldo.py","line":160,"evidence":"ClienteSecuencial(SALIDA_VALIDA, ServerError) sobre la misma instancia exige ['modelo','extractivo']; el equivalente E2E está en tests/server/e2e/test_respaldo_e2e.py:147. Quitar gemini.py:109 o leer modo antes de redactar hace fallar ambas."},
{"id":"F2","status":"resolved","severity":"medium","lens":"ai","title":"Los dobles solo lanzaban excepciones de Python","file":"tests/server/aplicacion/test_respaldo.py","line":108,"evidence":"El parametrize incluye httpx.ReadTimeout/ConnectTimeout/TimeoutException y genai APIError/ServerError/ClientError; errors.py:56 muestra que APIError hereda de Exception, así que un except estrecho deja fallar 6 casos más el secuencial (7)."},
{"id":"F4","status":"resolved","severity":"low","lens":"core","title":"Dependencia de atributos privados del SDK sin documentar","file":"tests/server/aplicacion/test_respaldo.py","line":243,"evidence":"Comentario añadido que explica el acoplamiento a _api_client._http_options."},
{"id":"F5","status":"open","severity":"low","lens":"core","title":"La prueba D9 sobre el cliente real es redundante con el espía y frágil ante el SDK","file":"tests/server/aplicacion/test_respaldo.py","line":240,"evidence":"Detecta las mismas mutaciones que test_d9_la_fabrica_por_defecto_usa_httpoptions...; solo aporta la comprobación de que el SDK acepta HttpOptions. Advisory: puede quedarse, ya está documentada."},
{"id":"F6","status":"open","severity":"low","lens":"core","title":"La prueba E2E de dos caídas seguidas no detecta ninguna mutación que no detecten ya las otras","file":"tests/server/e2e/test_respaldo_e2e.py","line":118,"evidence":"Con el modo rancio quitado, sigue pasando porque nunca hubo un éxito; el caso modelo->extractivo (línea 147) es el que discrimina. Advisory: candidata a eliminar como ruido o a conservar como regresión de caída sostenida."},
{"id":"F7","status":"open","severity":"low","lens":"core","title":"No leí src/server/http/app.py directamente","file":"src/server/http/app.py","line":1,"evidence":"OPEN: que crear_app(redactor=None) lea solo os.environ['GEMINI_API_KEY'] lo tomo de src/server/AGENTS.md y de lo que comprueba test_s12_2_crear_app_sin_gemini_api_key...; no lo verifiqué contra el código fuente."}
]}
```

## T11 — attempt 1

VERDICT: PASS

T11 cumple su "Done when" con el código que ya existe. El diff solo agrega dos archivos de prueba y no hace falta tocar producción, así que registrar el REPORTED con `--implementer self` es correcto. Leí `app.py`, `gemini.py`, `consultar.py` y `rutas.py` directamente.

## Lo que pediste comprobar

- **`crear_app(redactor=None)` lee solo `os.environ`:** sí. `src/server/http/app.py:52-54`, en el `lifespan`: `RedactorGemini(api_key=os.environ.get("GEMINI_API_KEY"))`, sin `dotenv` ni otra fuente. Cierra el F7 de la inspección anterior.
- **`HttpOptions(timeout=5000)` sin `retry_options`:** sí. `gemini.py:36`, con `TIMEOUT_MS = 5000` (línea 23); una sola llamada a `generate_content`, sin bucle.
- **El registro guarda `modo` extractivo tras un fallo:** sí, sin valor pegado. Todas las salidas por fallo pasan por `_respaldar` (`gemini.py:109`); `consultar.py:46` lee `redactor.modo` después de `redactar`; `RedactorExclusivo` (`rutas.py:32-34`) copia el `modo` bajo el candado.

## Cada punto del "Done when"

| Punto | Código | Prueba |
|---|---|---|
| S-12.1 | `gemini.py:79-83`, `:109` | Unitarias con 9 tipos de error más `TimeoutError`; E2E con fila `modo='extractivo'` |
| S-12.2 | `gemini.py:73-74` | Unitarias con `None`, `""` y espía de `genai.Client`; E2E con `delenv` y espía |
| `HttpOptions(timeout=5000)` sin `retry_options` | `gemini.py:36` | `test_d9_*` |
| E2E con Gemini caído, registrado | Ya existía | `test_respaldo_e2e.py` |

## TDD y evidencia

Sin rojo; vía de revisión: `execution.md:92` registra `TEST_REVIEWED` y `reviews.md:578-623` tiene el PASS tras reforzar las pruebas. Coincido con esa inspección. La fila RED de `execution.md:89` (dos rutas en un argumento, exit 4, 0 pruebas) no es evidencia de rojo. `redTests.changed: []`; ningún caso eliminado.

## Gates

Todos PASS según `.mandao/cache/MDO-0001/gates/T11-1.md`: test "23 passed" (solo los dos archivos afectados), metrics "7 passed, 246 deselected". La salida de `verify` no está en el paquete (F3, advertencia).

## Módulos y lente AI

`src/server/AGENTS.md` ya describe el respaldo, el `modo`, la fábrica con timeout y la lectura de la clave. Sin violaciones de límites. Lente AI: no se filtran la clave ni la pregunta, un solo intento, respaldo determinista.

## Findings (JSON)

```json
{"version":1,"findings":[
{"id":"F1","status":"resolved","severity":"low","lens":"core","title":"crear_app(redactor=None) lee la clave solo de os.environ (verificado en el código)","file":"src/server/http/app.py","line":52,"evidence":"`app.state.redactor = redactor or RedactorGemini(api_key=os.environ.get(\"GEMINI_API_KEY\"))` dentro del lifespan; sin dotenv ni otra fuente. Cierra el F7 OPEN de la inspección de pruebas."},
{"id":"F2","status":"open","severity":"low","lens":"core","title":"`redactor or ...` usa el valor de verdad en vez de `is None`","file":"src/server/http/app.py","line":52,"evidence":"Un Redactor inyectado que defina __bool__ o __len__ y se evalúe como falso se sustituiría en silencio por RedactorGemini. Advisory: `redactor if redactor is not None else RedactorGemini(...)`."},
{"id":"F3","status":"open","severity":"low","lens":"core","title":"El gate test corrió solo los 23 casos afectados, no el comando verify de la tarea","file":".mandao/cache/MDO-0001/gates/T11-1.md","line":46,"evidence":"'collected 23 items'; `verify: uv run pytest tests/server/aplicacion tests/server/e2e -q` no aparece ejecutado en el paquete. Sin cambios de producción el riesgo es mínimo. Advisory: adjuntar esa salida al cerrar la tarea."},
{"id":"F4","status":"open","severity":"low","lens":"core","title":"El E2E importa un doble desde otro módulo de prueba","file":"tests/server/e2e/test_respaldo_e2e.py","line":17,"evidence":"`from test_flujo_consulta import EmbeddingsOraculo` depende del rootdir/import mode de pytest. Advisory: moverlo a un conftest.py o a un módulo de dobles compartido."},
{"id":"F5","status":"open","severity":"low","lens":"core","title":"La prueba D9 sobre el cliente real depende de atributos privados del SDK","file":"tests/server/aplicacion/test_respaldo.py","line":247,"evidence":"`cliente._api_client._http_options`; está documentado en el comentario y es redundante con el espía. Advisory, heredado de la inspección de pruebas (F5)."},
{"id":"F6","status":"open","severity":"low","lens":"core","title":"Sigue apareciendo la PytestUnraisableExceptionWarning de QdrantClient.__del__ en otro hilo","file":"src/server/http/app.py","line":61,"evidence":"La salida del gate test muestra 'sqlite3.ProgrammingError: SQLite objects created in a thread can only be used in that same thread' desde QdrantClient.__del__. No lo introduce T11 y no rompe ninguna prueba; advisory para revisar la mitigación de app.py:59-61."}
]}
```

## T12 — attempt 1

VERDICT: PASS

Reviso el estado actual del código. `middleware.py`, `problemas.py` y `app.py` no cambian en este diff. Los resultados de pruebas que cito vienen de los gates del pack y de las dos mutaciones. Yo no ejecuté nada.

## Conformidad con la spec

- **S-13.1 y AC-15: se cumple.** Si la búsqueda lanza, la API responde 500 `application/problem+json` con exactamente `type`, `title`, `status`, `detail` y `requestId`; `requestId` coincide con `X-Request-Id` y `detail == DETALLES[500]`. La excepción la captura `MiddlewareSolicitud`, por dentro de `ServerErrorMiddleware`.
- **S-13.1/C1 y AC-15/C1: se cumple** para búsqueda e insert. El marcador, la lista de textos y `SELECT * FROM fragmentos` del mensaje de prueba no aparecen en el cuerpo.
- **S-11.2: se cumple.** Mismo 500 genérico, sin la respuesta del redactor.
- **NFR-4: se cumple.** La línea JSON lleva `requestId`, `codigo: 500` y `error` con el tipo; ni la pregunta ni el mensaje aparecen en `caplog.text` (DEBUG, todos los loggers). Una sola línea con el `requestId`.

## Sobre D8

T12 cumple sus cuatro criterios de comportamiento. D8 (`design.md:128`) y el "What" de T12 (`tasks.md:427`) todavía hablan de un handler de `Exception`; la justificación de la desviación solo está en `_log/reviews.md:480`. Registrarla en D8 antes de cerrar la spec. No bloquea T12 (F1).

## Las tres comprobaciones pedidas

- **`detail` genérico:** sí, fijado por igualdad exacta en dos pruebas.
- **La pregunta no va al log:** sí, con marcador único en los dos fallos; T12-2 lo confirma.
- **Lista de cadenas prohibidas:** basta hoy; hueco no bloqueante (F2): falta la ruta temporal real, `fragmentos` y `Data/`, y el caso del insert no fija el conjunto de claves del cuerpo.

## TDD y pruebas

Evidencia por mutación: T12-1 (`detail=str(error)`) mata 4 casos y T12-2 (log con `str(error)`) mata los 2 de NFR-4. `redTests.changed` vacío. ASSUMPTION: el hash de reversión `e3b0c44298fc` es el SHA-256 vacío (diferencia vacía tras revertir). Sin pruebas innecesarias.

## Cambio fuera de la lista de archivos

`tests/server/aplicacion/test_respaldo.py:234`: solo el comentario `# pragma: allowlist secret`; aserción intacta (F3, resuelto). El gate se corrigió en `9b2e798`.

## Otros puntos

`src/server/AGENTS.md` ya describe el 500 en el middleware. Sin fronteras rotas. OPEN (advisory): FR-13 dice "el detalle queda solo en el log", pero el log solo guarda el tipo; coherente con NFR-4, decisión de producto.

## Findings (JSON)

```json
{"version":1,"findings":[
{"id":"F1","status":"open","severity":"medium","lens":"core","title":"D8 y el What de T12 aún describen un handler de Exception; la desviación al middleware solo consta en _log/reviews.md","file":"especificaciones/MDO-0001-consultar-la-base-documental-con-fuentes/design.md","line":128,"evidence":"design.md:128 dice que hay handlers propios para `RequestValidationError` (422), `HTTPException` y `Exception` (500); tasks.md:427 habla del handler de `Exception`; la implementación está en src/server/http/middleware.py:42-47 y la justificación (ServerErrorMiddleware vuelve a lanzar la excepción) solo está en _log/reviews.md:480. Hay que registrarla en D8 antes de cerrar la spec; no bloquea T12."},
{"id":"F2","status":"open","severity":"low","lens":"security","title":"A la lista de cadenas prohibidas le faltan la ruta temporal real, la tabla fragmentos y Data/, y el caso parametrizado no fija el cuerpo completo","file":"tests/server/http/test_errores.py","line":248,"evidence":"PROHIBIDOS_EN_CUERPO no incluye str(entorno.ruta_sqlite) ni str(tmp_path) (bajo /private/var en macOS), 'fragmentos' (la tabla del SQL de prueba) ni 'Data/'. test_s13_1_c1 solo fija `detail`. Hoy lo cubren la igualdad exacta de `detail` y MARCA_MENSAJE; recomiendo un assert sobre el cuerpo completo, sin contar requestId."},
{"id":"F3","status":"resolved","severity":"low","lens":"security","title":"Cambio fuera de la lista de archivos: pragma allowlist en test_respaldo.py","file":"tests/server/aplicacion/test_respaldo.py","line":234,"evidence":"Solo se añade el comentario `# pragma: allowlist secret`; la aserción no cambia y 'clave-falsa' es un valor de prueba. Lo destapó el gate de secretos, ahora corregido en 9b2e798 para escanear archivos no trackeados."}
]}
```

## T13 — attempt 1

VERDICT: PASS

The model name isn't something I can give. My operating instructions say not to state it, and Mandao records who reviewed from what it invoked.

T13 is a narrow fix and it is correct against D9 as amended. I found nothing blocking, but the module's `AGENTS.md` (`src/server/AGENTS.md`) needs a one-line update before close.

**Checks**
1. **Spec and decision D9:** The local timeout is still `TIMEOUT_MS = 5000`. The factory now also sets `X-Server-Timeout: 10`. There are still no `retry_options`, and the test checks that `retry_options is None`. I checked the claim that "the SDK does not overwrite the header" against the installed SDK, in `.venv/lib/python3.13/site-packages/google/genai/_api_client.py:238-243`. `populate_server_timeout_header` only sets the header when `'X-Server-Timeout' not in headers`. That check is case-sensitive, and the code uses exactly that spelling. AC-16 and S-12.1 keep working: if a call fails or times out, the answer still falls back to extractive mode, and that path is unchanged.
2. **Tests:** The new test builds the real `types.HttpOptions` and replaces only `genai.Client`, so it makes no network call. It checks the 5 s client timeout, the 10 s header and that there are no retries. The test is meaningful and not noise. No test cases were removed.
3. **`AGENTS.md`:** Line 21 still describes the factory as `HttpOptions(timeout=5000)` and does not mention the server-timeout header (F1).
4. **Clean code:** The new constant `SERVER_TIMEOUT_S` is named and commented, so it is not a magic number. The change follows the exemplar file (the file itself), keeps the deferred import in the single place that imports the SDK, and swallows no errors.
5. **AI lens (`ai-prompt`):** The prompt, the model and `VERSION_PROMPT` did not change. The API key is still passed only to the client, and logs are unchanged.
6. **TDD:** `loop.tdd.red=true`, the evidence is `red` and `redTests.changed` is empty, so no red test was weakened.
7. **Module boundaries:** The change stays inside `infraestructura/redactor`. No boundary is crossed.

**What the gate results show:** format, lint, typecheck, secrets, sast and metrics passed. The "test" gate ran only the impacted file: 34 passed in 0.18s. Audit and build were skipped. I have no evidence that the full suite (`uv run pytest`) ran for this attempt.

**OPEN:** D9 says the fix was "Validado contra el API real". The pack contains no output from that check, so I have not verified it.

## Findings (JSON)

```json
{"version":1,"findings":[
{"id":"F1","status":"open","severity":"medium","lens":"core","title":"Module AGENTS.md not updated for the X-Server-Timeout header","file":"src/server/AGENTS.md","line":21,"evidence":"Still says the default factory creates genai.Client with `HttpOptions(timeout=5000)`; it does not mention `headers={'X-Server-Timeout': '10'}` or that the API rejects server deadlines under 10 s. That was the cause of the bug where no real-key call reached the model. Add it in this task's commit or at close."},
{"id":"F2","status":"open","severity":"low","lens":"core","title":"Test matches the header name case-insensitively, but the SDK check is case-sensitive","file":"tests/server/infraestructura/redactor/test_gemini.py","line":245,"evidence":"The test lowercases header keys before looking up 'x-server-timeout'. The SDK only skips adding its own header when the exact key 'X-Server-Timeout' is present (_api_client.py:242). If someone renamed the key to 'x-server-timeout', the test would still pass, but the SDK would add 'X-Server-Timeout: 5' next to it. Advisory: assert the exact key."},
{"id":"F3","status":"open","severity":"low","lens":"ai","title":"No recorded evidence of the real-API check","file":"src/server/infraestructura/redactor/gemini.py","line":207,"evidence":"D9 says the fix was 'Validado contra el API real', but the gate results contain no such output. Advisory: record the check (status code or mode=modelo, with no key or content) in the execution log."}
]}
```

## T14 — attempt 1

VERDICT: PASS

T14 passes with no blocking findings. The production change is one function: each fragment sent to Gemini now carries a `documento > sección` line at the top. The other two files are small doc and test follow-ups from the T13 review.

**1. Spec and decisions.**
- **D7:** each `<fragmento id="N">` now opens with a `documento > sección` line, then the text. That is exactly what D7's T14 note asks for.
- **AC-4/C1 and AC-5:** the output guardrail (`validar_salida`), the code-built "No encontré información sobre ..." phrase and the fallback to the extractive mode are unchanged. The `test_S_5_1_*` tests still cover them.
- **S-4.1:** the Leader's smoke test with the real key returned `$50.000.000` with `modo=modelo` and cited only fragment 1. I am relying on what you told me here; that run's output is not in the pack.

**2. Test policy.** The gates the pack reports all passed. Build and audit were skipped, and there is no shell here to check beyond that. Nothing was deleted from the test file. Two existing assertions were edited, and both edits are fine:
- **D7 test:** the regex went from `\s*` to `\n[^\n]*\n`. The new format required the change, and it is a tighter check on structure.
- **T13 test:** the header check is now the exact `X-Server-Timeout` key instead of a case-insensitive match. That is also stricter.

The two new tests aimed at T14 are meaningful. `test_T14_D7_...` checks that each fragment's own name and section sit inside its own tag. `test_T14_D5_...` checks that injected tags in the document name or section are neutralised. Three of the new S-4.1 tests mostly re-check the existing guardrail (advisory F2 below).

**3. `src/server/AGENTS.md`.** It describes the new fragment format, the neutralisation of the name/section line and the exact header. That resolves the T13 advisory.

**4. Clean code.** The change follows the existing pattern in `gemini.py` and reuses `_neutralizar`. No logic is duplicated, there are no magic numbers and no errors are swallowed.

**5. Lenses.**
- **Security:** the new name/section line goes through the same tag neutralisation as the text and the question, and the test proves it. It is data in `contents`, not part of the system instruction. Logs still record only the exception type. The confidential document is still excluded at load time.
- **AI:** the model input changed in a meaningful way while `prompt.md` stayed at v1 (advisory F1).

**6. TDD.** The log has red evidence for T14 attempt 1: the tester's run of `test_gemini.py` failed with exit 1. I checked the edited tests and none were weakened to pass.

**7. Module boundaries.** All changes stay inside `infraestructura/redactor`. The new test that goes through `consultar` only uses public interfaces and test doubles.

## Findings (JSON)

```json
{"version":1,"findings":[
{"id":"F1","status":"open","severity":"low","lens":"ai","title":"prompt.md v1 does not tell the model that the first line of each fragment is its document > section","file":"src/server/infraestructura/redactor/prompt.md","line":10,"evidence":"The task brief lists prompt.md, but it was not changed. The Entrada section still says only `<fragmento id=\"N\">...</fragmento>`. The fragment format changed while VERSION_PROMPT stays v1 and model-registry.md has no note. The smoke test shows the model uses the line correctly anyway. Advisory: if the prompt is changed to explain the line, raise VERSION_PROMPT to v2 and update model-registry.md, or note the contents-format change in the registry."},
{"id":"F2","status":"open","severity":"low","lens":"core","title":"Three S-4.1 tests mostly re-check the existing guardrail or repeat what the test double returns","file":"tests/server/infraestructura/redactor/test_gemini.py","line":343,"evidence":"test_T14_S_4_1_respuesta_validada_... asserts what ClienteDoble was told to return. The ..._se_descarta_al_extractivo test and the ..._en_consultar_... test exercise the guardrail and consultar, which already behaved this way before T14. They are useful regression cases for the reported mixing bug but are not red evidence for T14. Advisory: the tests that actually drive T14 are test_T14_D7_... and test_T14_D5_...."},
{"id":"F3","status":"resolved","severity":"low","lens":"core","title":"T13 advisory: AGENTS.md did not mention the X-Server-Timeout header","file":"src/server/AGENTS.md","line":21,"evidence":"The RedactorGemini entry now documents HttpOptions(timeout=5000, headers={\"X-Server-Timeout\": \"10\"}) and the new fragment format."},
{"id":"F4","status":"resolved","severity":"low","lens":"core","title":"T13 advisory: the header assertion was case-insensitive","file":"tests/server/infraestructura/redactor/test_gemini.py","line":280,"evidence":"It now asserts (opciones.headers or {}).get(\"X-Server-Timeout\") == \"10\" with the exact key, which is stricter."}
]}
```

Files reviewed:
- /Users/jguzman/GitHub/Projects/asistente-asesores.worktrees/MDO-0001-consultar-la-base-documental-con-fuentes/src/server/infraestructura/redactor/gemini.py
- /Users/jguzman/GitHub/Projects/asistente-asesores.worktrees/MDO-0001-consultar-la-base-documental-con-fuentes/src/server/infraestructura/redactor/prompt.md
- /Users/jguzman/GitHub/Projects/asistente-asesores.worktrees/MDO-0001-consultar-la-base-documental-con-fuentes/tests/server/infraestructura/redactor/test_gemini.py
- /Users/jguzman/GitHub/Projects/asistente-asesores.worktrees/MDO-0001-consultar-la-base-documental-con-fuentes/src/server/AGENTS.md

## T15 — attempt 1

**VERDICT: PASS**

The change does what D9 now asks for. The global lock is gone, and a `threading.BoundedSemaphore` built from `GEMINI_MAX_CONCURRENCIA` caps simultaneous calls, default 5. An invalid value raises `ValueError` when `crear_app` runs, so the app does not start. Each call's `modo` now comes back in `RespuestaRedactada.modo`. A 429 falls back to extractive with a 200, and the log records only the exception type and the integer code. D13 holds: still one worker and one Qdrant client.

**Evidence**
- **Gates:** all configured gates passed in `.mandao/cache/MDO-0001/gates/T15-1.md` (32 passed in the gate run, 9 passed for metrics); build and audit were skipped. For the 3 s p95 target I only have the Leader's real-key measurement (median p95 1.02 s, 19 `modelo` / 7 `extractivo`, all 200). It is recorded in `execution.md` but no gate output shows it, so I take it as reported and have not verified it.
- **TDD:** the red run is recorded (`execution.md` line 112: tester's tests, pytest exit 1). The one changed red test, `test_dos_peticiones_concurrentes_registran_cada_una_su_propio_modo`, was not weakened. It still forces the interleaving that corrupts `self.modo`, and its assertion is unchanged. The only edit is that each call also returns its own `modo`, which is the contract D9 introduces. Without the lock, an implementation that still read `redactor.modo` would fail it.
- **Contract:** `extractivo.py` and `gemini.py` both fill `modo` on every path. `consultar.py` prefers `redactada.modo` and falls back to `redactor.modo`. Logs never carry the key, the question, the SDK message or `RESOURCE_EXHAUSTED`, and the 429 test asserts this.
- **Module boundaries:** the dataclass field is added on the domain side, the route reads only public contracts, and only `gemini.py` imports `google-genai`. No violations.
- **AI lens:** the prompt is unchanged, there are no retries (consistent with the rejected-alternative note in D9), and the fallback is extractive.

The Implementer's three flags are all acceptable. The `consultar.py` edit is the minimal change the D9 contract needs. Keeping `RedactorGemini.modo` is harmless because the route never reads it when the response carries `modo`. The `ValueError` on an invalid limit matches D9's "detiene el arranque". I also noticed `extractivo.py` was changed outside the task's `files` and was not flagged (F1).

None of the findings below blocks. F2 is the one worth fixing before the commit.

## Findings (JSON)

```json
{"version":1,"findings":[
{"id":"F1","status":"open","severity":"low","lens":"core","title":"Two source files changed outside the task's declared files","file":"src/server/infraestructura/redactor/extractivo.py","line":22,"evidence":"Brief files list rutas.py, app.py, gemini.py, puertos.py and the test. aplicacion/consultar.py (flagged by the Implementer) and redactor/extractivo.py (not flagged) were also changed. Both are minimal and required by D9's 'El modo viaja en RespuestaRedactada.modo'. Record both in the task's files at close."},
{"id":"F2","status":"open","severity":"medium","lens":"core","title":"AGENTS.md entries for consultar.py and extractivo.py were not updated","file":"src/server/AGENTS.md","line":272,"evidence":"The aplicacion/consultar.py entry still says it registers 'con el modo del redactor' and that 'modo es ninguno sin redacción, o el modo del redactor'. It should say it prefers RespuestaRedactada.modo and falls back to Redactor.modo. The extractivo.py entry does not mention that it now fills modo='extractivo' in the response. The rutas.py and puertos.py entries do describe the new flow, so this is imprecise rather than contradictory."},
{"id":"F3","status":"open","severity":"low","lens":"core","title":"Startup failure on an invalid GEMINI_MAX_CONCURRENCIA has no test","file":"src/server/http/app.py","line":336,"evidence":"D9 says 'un valor no entero o menor que 1 detiene el arranque'. _limite_concurrencia raises ValueError for both, but no test covers 'abc', '0' or max_concurrencia=0."},
{"id":"F4","status":"open","severity":"low","lens":"core","title":"Concurrency-limit test is named for S-14.1 but does not exercise S-14.1","file":"tests/server/http/test_consultar_api.py","line":632,"evidence":"test_s14_1_con_mas_consultas_que_el_limite_nunca_hay_mas_en_vuelo_que_el_limite checks the semaphore peak. S-14.1 is about the body having exactly respuesta/fuentes/estado plus X-Request-Id, which the existing s14_1 tests already cover. The name misleads traceability."},
{"id":"F5","status":"open","severity":"low","lens":"core","title":"Stale type-ignore and a tight timing assertion in the new tests","file":"tests/server/http/test_consultar_api.py","line":577,"evidence":"'# type: ignore[call-arg]' is now unnecessary because RespuestaRedactada has modo; mypy only covers src, so nothing flags it. 'assert duracion < 2 * ESPERA_S' (0.6 s for 5 requests with real search) could flake on a slow CI runner; the redactor.pico == 5 assertion already proves the calls overlap."},
{"id":"F6","status":"open","severity":"low","lens":"performance","title":"Requests waiting on the semaphore are not bounded by the 3 s target","file":"src/server/http/rutas.py","line":409,"evidence":"With 5 calls in flight, each with a 5 s local timeout, a 6th request can wait about 5 s for a permit and then up to 5 s more for its own call. This follows the PE decision (cap of 5), and the Leader's measurement used exactly 5 concurrent requests. Waits beyond the cap are not measured. A timed acquire that falls back to extractive is a possible follow-up, not required by D9."}
]}
```

Files referenced:
- /Users/jguzman/GitHub/Projects/asistente-asesores.worktrees/MDO-0001-consultar-la-base-documental-con-fuentes/.mandao/cache/MDO-0001/reviews/T15-1-pack.md
- /Users/jguzman/GitHub/Projects/asistente-asesores.worktrees/MDO-0001-consultar-la-base-documental-con-fuentes/src/server/AGENTS.md
- /Users/jguzman/GitHub/Projects/asistente-asesores.worktrees/MDO-0001-consultar-la-base-documental-con-fuentes/src/server/http/app.py
- /Users/jguzman/GitHub/Projects/asistente-asesores.worktrees/MDO-0001-consultar-la-base-documental-con-fuentes/src/server/http/rutas.py
- /Users/jguzman/GitHub/Projects/asistente-asesores.worktrees/MDO-0001-consultar-la-base-documental-con-fuentes/tests/server/http/test_consultar_api.py
- /Users/jguzman/GitHub/Projects/asistente-asesores.worktrees/MDO-0001-consultar-la-base-documental-con-fuentes/especificaciones/MDO-0001-consultar-la-base-documental-con-fuentes/_log/execution.md

## T16 — test review 1 (via claude)

TEST REVIEW: PASS

## Assertions

Each changed existing test was checked against its HEAD version in the pack diff and against the current file; none of the changes weakens an assertion.

- `tests/server/http/test_consultar_api.py`: the `# type: ignore[call-arg]` removal on `RespuestaRedactada(..., modo=modo)` is typing only. `test_s12_1_cinco_consultas_...` dropped `duracion < 2 * ESPERA_S`; `redactor.pico == 5` (calls inside `redactar` at the same moment, counted under a lock around a 0.3 s sleep) proves all five overlapped, which the wall-clock bound only suggested and could miss on a slow CI runner: stronger. `test_s14_1_...` renamed to `test_s12_1_con_mas_consultas_que_el_limite_...`; `pico == 2` and the per-request mode checks intact.
- `tests/server/infraestructura/busqueda/test_indice.py`: `_fts` reduces the searched word to roots before `MATCH` (the index now stores roots; raw words would always return 0 and make the absence checks pass for the wrong reason). In the confidential-leak test, `unicos` also drops restricted terms whose roots all appear among official roots (false positives, not leaks). It still catches a real leak: `"INT-8457-SECRET-782" in unicos`, `_fts(conexion, "INT-8457") == 0` (phrase `int 8457`), payload, point count, embedded texts and `fragmentos.documento` checks unchanged and independent of stemming.
- `tests/server/infraestructura/busqueda/test_buscador.py`: `test_s81_...` expects `set(raices(...))` instead of literal words; stop-word exclusion, `"..." OR "..."` shape and no-operator checks unchanged. Close to circular; `test_fts.py` pins the stemming itself (advisory).
- `tests/server/e2e/test_arranque_indice.py`: MATCH literal `"Impulso"` → `"impuls"` (stored stem); `encontrados >= 1` unchanged.
- `tests/server/evals/test_evals.py`: version guard asserts `"v3"`; docstring, report title and one test name say v3; no threshold relaxed (EV-1 >= 0.90, EV-2 >= 0.90, EV-3 <= 0.10, EV-4/5 == 1.00, EV-7 >= 0.90, margin 0.005).

Verified: `uv run pytest tests/server -q` → 267 passed, 9 deselected; evals 9 passed (EV-1=0.982 … EV-7=1.000). The runner's "test" gate failure is `tests/fixtures/consultas.json` passed to pytest as a test path, not a test failure.
- `tests/server/infraestructura/redactor/test_proveedores.py` and `tests/server/infraestructura/redactor/test_extractivo.py` (red tests changed): uncommitted red tests for scope the PE discarded (LLM_PROVIDER version of T16; the 80 % filter rejected in C-10(2)/D12). `test_proveedores.py` does not exist in the worktree; `test_extractivo.py` is unchanged from HEAD; no `s_6_2` or `LLM_PROVIDER` tests remain. No committed coverage lost.
- `tests/server/infraestructura/busqueda/test_fts.py` (new): S-3.3 at unit level ("pequeño", "pequeños", "pequenos" share a root; the PE question through FTS over `Data/` returns `Crédito Productivo Impulso` first); red evidence recorded before the code existed (import error on `raices`, exit 2).
- Discarded red node ids from the LLM_PROVIDER version of T16, no longer present in the file (no `LLM_PROVIDER` tests remain): `tests/server/http/test_consultar_api.py::test_s12_3_con_clave_pero_sin_llm_provider_responde_extractivo_y_no_crea_el_cliente`, `tests/server/http/test_consultar_api.py::test_s12_3_un_llm_provider_desconocido_detiene_crear_app`, `tests/server/http/test_consultar_api.py::test_s12_1_sin_cupo_tras_la_espera_acotada_responde_extractivo_sin_esperar_al_modelo`.

## T16 — attempt 1

VERDICT: PASS

1. Spec conformance. C-10 (1): `raices()` in `fts.py` is one normalization shared by the index (`indice.py`) and the question (`consulta_fts`); accents removed before stemming, only FTS changes, embeddings keep `texto_indexable`, `VERSION_FORMATO` unchanged, as D4 says. C-10 (2): the 80 % filter is rejected in D12 and listed as a README limitation; no filter code. C-10 (3): `consultas.json` v3 with 80 questions including c35 and c36; D4 records EV before/after, thresholds unchanged at 0.60 / 0.525 with a 0.008 margin, in-sample rewording of c40 disclosed. AC-3 / AC-11: EV-1 0.982, EV-2 1.000, EV-3 0.000 per the gate output. Every T16 "Done when" item is met.
2. Removed test cases: uncommitted red tests for discarded scope (`test_proveedores.py` does not exist; `test_extractivo.py` unchanged from HEAD; no `s_6_2` or `LLM_PROVIDER` tests remain). No existing coverage lost. Reason per C-10(2)/(3).
3. AGENTS.md: `src/server/AGENTS.md` covers `raices`, FTS indexing stems, the flow line, and `modo` from `RespuestaRedactada.modo`.
4. Clean code: no duplicated logic (index and query share `raices`), no swallowed errors, no business magic numbers; the mypy override for a stub-less package is narrow and commented.
5. Lenses: no risk tags. Security as core: the question is still bound with `MATCH ?`, stems quoted with `"` escaped; the leak test still holds.
6. TDD: red evidence recorded for `test_fts.py`; red tests changed belong to discarded scope.
7. Module boundaries: `indice.py` importing `fts.raices` stays inside `infraestructura/busqueda`.
8. New dependency: `py-rust-stemmers==0.1.8` pinned, MIT (installed METADATA), fits `standards.md` line 62; named by the PE in C-10.

## Findings (JSON)

```json
{"version":1,"findings":[
{"id":"F1","status":"open","severity":"low","lens":"core","title":"Removed red test cases have no recorded reason in the Mandao removal record","file":"especificaciones/MDO-0001-consultar-la-base-documental-con-fuentes/_log/state.yml","line":460,"evidence":"Pack: 'Reason recorded by the Leader: missing'. Uncommitted red tests for scope the PE discarded (LLM_PROVIDER; the 80 % filter rejected in C-10(2)/D12); no coverage lost. The Leader should write that reason into the removal record."},
{"id":"F2","status":"open","severity":"low","lens":"core","title":"AGENTS.md cites only C-9 for the v3 calibration","file":"src/server/AGENTS.md","line":12,"evidence":"The config.py bullet says 'calibrados contra tests/fixtures/consultas.json@v3 ... (D4, C-9)'; the v3 recalibration comes from C-10. Advisory."},
{"id":"F3","status":"open","severity":"low","lens":"core","title":"test_s81 expected terms are derived with the function under test","file":"tests/server/infraestructura/busqueda/test_buscador.py","line":394,"evidence":"'set(raices(\"monto máximo ...\")) <= plano' compares against raices() itself; listing the expected stems literally would pin the behavior. test_fts.py covers stemming separately. Advisory."},
{"id":"F4","status":"resolved","severity":"low","lens":"core","title":"Wall-clock assertion in the concurrency test replaced by the peak check","file":"tests/server/http/test_consultar_api.py","line":511,"evidence":"'duracion < 2 * ESPERA_S' removed; 'redactor.pico == 5' proves all five calls overlapped; the limit test was renamed from s14_1 to s12_1, as T16 asked."}
]}
```
