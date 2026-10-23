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
