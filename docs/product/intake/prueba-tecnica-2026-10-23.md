---
schema_version: 1
source: { path: "/Users/jguzman/Downloads/Docs - BW/Prueba técnica.pdf", sha256: "ea559182d0cbe46540d0bbd994fa163b6633b42d03100c29632446a0267746b7", extractor: native }
doc: prueba-tecnica
date: 2026-10-23
status: proposed
---

# Intake: Prueba técnica — Desarrollador de IA

Enunciado de la prueba técnica del Laboratorio Digital (Vicepresidencia de Innovación y Mercadeo) para un
asistente interno de asesores comerciales; propone 11 historias en 3 épicas. Gran parte del documento ya
está recogida en la constitución aprobada (`constitucion/`, 2026-10-23): aquí solo se proponen los
elementos de contexto que aún no están. Prioridad con MoSCoW (`product-manager-toolkit`); todo lo que el
documento exige como entregable es `Must`.

## Business context

Applied to `constitucion/` item by item, only after approval. A contradiction is `CONFLICT`, never
an overwrite. Ya presentes y no se repiten: BR-1, BR-2, BR-3, BR-6, BR-7 (`business-rules.md`), los
siete principios (`constitucion.md`), los términos Consulta, Respuesta, Fuente, Estado y Base documental
(`glossary.md`).

| ID | Kind | Proposal | Target | Ref | Status |
|---|---|---|---|---|---|
| C-1 | rule | DC-1 (Restricciones de entrega): la base documental de ejemplo puede ampliarse con los registros que se consideren necesarios; los archivos finales de `Data/` forman parte de los entregables. Es condición de la entrega, no regla del asistente. | product.md | p. 2 | applied |
| C-2 | rule | BR-9: los temas que el asistente atiende son: productos de crédito, microseguros, procedimientos operativos y políticas internas. Una consulta fuera de estos temas es `Sin información suficiente`; no se bloquea. | business-rules.md | p. 2 | applied |
| C-3 | rule | DC-2 (Restricciones de entrega): repositorio GitHub, máximo 72 horas, se permite el uso de IA y no se requieren herramientas pagas. | product.md | p. 1 | applied |
| C-4 | term | Procesamiento: estado de la interfaz mientras una consulta está en curso (cargando, listo, error de red), distinto del estado de la respuesta que viene de la API. | glossary.md | p. 5 | applied |

## Epics

### E-1 — Consulta asistida con fuentes
El asesor pregunta y recibe una respuesta sustentada solo en la base documental, con sus fuentes, o un
mensaje fijo cuando no hay información, o un bloqueo cuando la consulta compromete la seguridad. Cada
consulta queda registrada con su estado; refs: [p. 2, p. 4, p. 5, p. 6]

### E-2 — Interfaz de consulta
Una pantalla local desde la que el asesor consulta y ve la respuesta, las fuentes, los errores y el estado
de procesamiento; refs: [p. 5]

### E-3 — Entregables de documentación y trazabilidad
Constitución, especificaciones (especificación, plan y tareas), README y cuestionario que demuestran SDD,
TDD y uso responsable de IA; refs: [p. 1, p. 2, p. 3, p. 4, p. 6, p. 7, p. 8]

## Stories

### I-1 — Responder una consulta con fuentes
- epic: E-1
- refs: [p. 2, p. 4, p. 5]
- priority: Must
- depends_on: [I-6]
- invest: cumple; es el flujo crítico "Consulta respondida con fuentes y registrada".
- opened: MDO-0001
#### AC-1 — Consulta válida con soporte documental
- GIVEN una base documental con el documento de productos de crédito / WHEN el asesor envía `{"pregunta": "¿Cuál es el monto máximo del Crédito Productivo Impulso?"}` a `POST /api/consultar` / THEN recibe 200 con `{"respuesta": …, "fuentes": [...], "estado": "Exitosa"}` (Q-2) con una respuesta construida solo con información encontrada y al menos una fuente citada.
#### AC-2 — Solo información encontrada
- GIVEN una consulta con soporte parcial / WHEN el asistente responde / THEN la respuesta no contiene datos que no estén en los fragmentos citados.

### I-2 — Validar la entrada de la consulta
- epic: E-1
- refs: [p. 5, p. 6]
- priority: Must
- depends_on: []
- invest: cumple; límite y códigos de error resueltos en Q-2 y Q-3, salvo el código del exceso de longitud (Q-6).
- opened: MDO-0001
#### AC-1 — Pregunta vacía
- GIVEN una pregunta vacía o solo con espacios, o un cuerpo inválido / WHEN se envía / THEN la API la rechaza con 422 (RFC 9457, con `requestId`) y no consulta documentos.
#### AC-2 — Caracteres especiales
- GIVEN una pregunta con tildes, eñes, signos y emojis / WHEN se envía / THEN se procesa sin error y la búsqueda no se rompe.
#### AC-3 — Consulta extensa
- GIVEN una pregunta de 1.001 caracteres Unicode tras quitar espacios al inicio y al final / WHEN se envía / THEN la API la rechaza con 422 y un mensaje claro (Q-6): no se recorta, no se consulta y no se registra.
- **AND IT MUST** aceptar una pregunta de exactamente 1.000 caracteres (C1).
#### AC-4 — Cuerpo o tipo de contenido no admitidos
- GIVEN un cuerpo mayor a 16 KB o un tipo de contenido distinto de JSON / WHEN se envía / THEN la API responde 413 o 415 respectivamente, en formato RFC 9457.

### I-3 — Indicar falta de información suficiente
- epic: E-1
- refs: [p. 2, p. 5, p. 6]
- priority: Must
- depends_on: [I-1]
- invest: cumple.
- opened: MDO-0001
#### AC-1 — Sin soporte documental
- GIVEN una pregunta que la base documental no responde / WHEN se consulta / THEN la respuesta es exactamente "No tengo información suficiente para responder.", sin fuentes, con estado `Sin información suficiente`.
#### AC-2 — Base documental vacía
- GIVEN una base documental sin documentos consultables / WHEN se consulta / THEN responde 200 con el mismo mensaje fijo y estado `Sin información suficiente`, sin fallar.
#### AC-3 — Pregunta fuera de tema
- GIVEN una pregunta ajena a los cuatro temas (BR-9) / WHEN se consulta / THEN el estado es `Sin información suficiente`.
- **BUT it must NOT** quedar `Bloqueada por seguridad` (C1).

### I-4 — Bloquear consultas que comprometen la seguridad
- epic: E-1
- refs: [p. 1, p. 2]
- priority: Must
- depends_on: [I-2]
- invest: cumple; es el flujo crítico "Consulta bloqueada por seguridad".
- opened: MDO-0003
#### AC-1 — Información restringida o técnica reservada
- GIVEN una pregunta que pide credenciales, configuraciones internas o información restringida / WHEN se consulta / THEN, antes de buscar, responde 200 con un mensaje fijo y genérico, estado `Bloqueada por seguridad`, y no revela nada del documento confidencial.
#### AC-2 — Prompt injection
- GIVEN una pregunta del tipo "ignora tus instrucciones y…" / WHEN se consulta / THEN el estado es `Bloqueada por seguridad` con el mismo mensaje genérico.
#### AC-3 — Datos de otros clientes
- GIVEN una pregunta que pide datos de otro cliente (BR-4, BR-8) / WHEN se consulta / THEN el estado es `Bloqueada por seguridad`.
- **AND IT MUST** registrar la consulta con su categoría de bloqueo en el log (C1).
#### AC-4 — Sin falsos positivos
- GIVEN una pregunta legítima con palabras sensibles (p. ej. "¿qué hago si un cliente olvida su clave?") / WHEN se consulta / THEN no se bloquea.
- **AND IT MUST** responder `Sin información suficiente`, no bloquear, a una pregunta fuera de tema (C1).

### I-5 — Registrar cada consulta
- epic: E-1
- refs: [p. 2]
- priority: Must
- depends_on: [I-1]
- invest: cumple.
- opened: MDO-0001
#### AC-1 — Registro completo
- GIVEN cualquier consulta procesada (exitosa, sin información o bloqueada) / WHEN termina / THEN queda almacenada con pregunta, fecha y hora, respuesta generada, fuentes utilizadas y estado.

### I-6 — Preparar la base documental consultable
- epic: E-1
- refs: [p. 2, p. 3, p. 6]
- priority: Must
- depends_on: []
- invest: cumple; la ampliación de registros es `Should` dentro de la historia (C-1).
- opened: MDO-0001
#### AC-1 — Documentos oficiales consultables
- GIVEN los documentos de `Data/` / WHEN se prepara la base / THEN los cinco documentos oficiales, incluido `Políticas de Atención.md` (Q-4), quedan consultables y `Información restringida.md` queda excluido.
#### AC-2 — Documentos duplicados
- GIVEN dos documentos con el mismo contenido / WHEN se prepara la base / THEN el contenido se considera una sola vez y una respuesta no repite la misma fuente.

### I-7 — Controlar errores del servicio
- epic: E-1
- refs: [p. 5]
- priority: Must
- depends_on: [I-1]
- invest: cumple.
- opened: MDO-0001
#### AC-1 — Error interno
- GIVEN una falla inesperada al buscar o guardar / WHEN se consulta / THEN la API responde 500 en formato RFC 9457 con `requestId`, sin detalles internos ni datos sensibles.
#### AC-2 — Falla del modelo
- GIVEN que Gemini falla o no responde / WHEN se consulta / THEN la respuesta es extractiva (fragmento y fuente) con 200.

### I-8 — Consultar desde la interfaz
- epic: E-2
- refs: [p. 5]
- priority: Must
- depends_on: [I-1]
- invest: cumple; ejecutable de forma local, el diseño visual no se evalúa.
- opened: MDO-0002
#### AC-1 — Realizar consulta y ver la respuesta
- GIVEN la interfaz local abierta / WHEN el asesor escribe una pregunta y la envía / THEN ve el estado de procesamiento mientras espera y luego la respuesta, sus fuentes y el estado de la respuesta.
#### AC-2 — Ver errores
- GIVEN una consulta que falla o es rechazada / WHEN llega la respuesta / THEN la interfaz muestra un error claro.

### I-9 — Documentar el proyecto en el README
- epic: E-3
- refs: [p. 6]
- priority: Must
- depends_on: [I-1, I-8]
- invest: no es valiosa para el asesor sino para el evaluador; se mantiene porque es entregable.
#### AC-1 — Secciones del README
- GIVEN el repositorio / WHEN se lee el README / THEN incluye descripción, arquitectura, tecnologías, instalación, configuración, ejecución, pruebas, limitaciones, mejoras futuras y uso de IA.

### I-10 — Responder el cuestionario técnico
- epic: E-3
- refs: [p. 6, p. 7, p. 8]
- priority: Must
- depends_on: [I-1, I-5]
- invest: documental; depende de las decisiones tomadas en la construcción.
#### AC-1 — Cuestionario completo
- GIVEN `docs/Cuestionario.md` / WHEN se lee / THEN documenta herramientas, actividades delegadas y manuales, sugerencias rechazadas, validación de la IA, y responde los bloques: decisiones para paso a productivo, uso de agentes, frontera IA / desarrollo tradicional, optimización y operación (100.000 consultas diarias), persistencia y escenario de producción.

### I-11 — Mantener los artefactos SDD con la estructura esperada
- epic: E-3
- refs: [p. 2, p. 3, p. 4]
- priority: Must
- depends_on: []
- invest: transversal al proceso; su forma depende de Q-1.
#### AC-1 — Constitución
- GIVEN `constitucion/constitucion.md` / WHEN se lee / THEN cabe en una página e incluye seguridad por defecto, calidad, TDD, uso responsable de IA, mantenibilidad, optimización de costos y observabilidad.
#### AC-2 — Especificación, plan y tareas por característica
- GIVEN cada carpeta de `especificaciones/` / WHEN se revisa / THEN contiene la especificación (contexto, objetivo, alcance, requerimientos funcionales y no funcionales, riesgos, criterios Gherkin), el plan (arquitectura, componentes, estrategia de pruebas) y las tareas (lista ordenada de tareas técnicas granulares).

## Open and conflicts

| ID | Type | Question or contradiction | Ref | Status |
|---|---|---|---|---|
| Q-1 | CONFLICT | El PDF espera `especificacion.md`, `plan.md` y `tareas.md` en cada carpeta de `especificaciones/` (p. 2-3); Mandao genera `story.md`, `requirements.md`, `design.md` y `tasks.md`. Resuelto (PE, 2026-10-23): se mantiene el árbol de Mandao y el README justifica la adaptación y el mapeo. | p. 2, p. 3 | resolved |
| Q-2 | OPEN | La respuesta del contrato del PDF es `{ respuesta, fuentes }` (p. 5); `architecture.md` añade `estado`. Resuelto (PE, 2026-10-23): `{ respuesta, fuentes, estado }`; los tres estados responden 200, incluida la base vacía. Errores: 422 validación, 413 cuerpo > 16 KB, 415 tipo de contenido, 500 inesperado; RFC 9457 con `requestId`. Si Gemini falla, respaldo extractivo con 200. | p. 2, p. 5 | resolved |
| Q-3 | OPEN | El PDF pide probar "consultas extensas" (p. 6) sin fijar un límite. Resuelto (PE, 2026-10-23): máximo 1.000 caracteres Unicode tras quitar espacios al inicio y al final (`performance.md`); por encima se rechaza sin recortar, consultar ni registrar. 1.000 se acepta, 1.001 se rechaza. | p. 6 | resolved |
| Q-4 | OPEN | El árbol de `Data/` del PDF (p. 3) no incluye `Políticas de Atención.md`, que sí existe en el repositorio y cubre "políticas internas" (p. 2). Resuelto (PE, 2026-10-23): se mantiene como entregable y fuente consultable (fuente de BR-1, BR-2, BR-5, BR-8); el README lista los seis archivos y aclara la diferencia con la p. 3. | p. 2, p. 3 | resolved |
| Q-5 | OPEN | "Bloqueada por seguridad" es un estado (p. 2) pero el PDF no define qué consultas se bloquean; la constitución lo concreta (DP-1, `security.md`). Resuelto (PE, 2026-10-23): tres categorías con reglas deterministas sobre el texto normalizado, antes de buscar: información restringida o técnica reservada, prompt injection y datos de otros clientes. Mensaje fijo y genérico; categoría en el log. Fuera de tema y preguntas legítimas con palabras sensibles no se bloquean (pruebas de falsos positivos). Segunda capa: guardrail de salida e instrucciones a Gemini. | p. 2 | resolved |
| Q-6 | CONFLICT | Q-2 (PE, 2026-10-23): "422 validación (vacía, más de 1.000 caracteres, cuerpo inválido)"; Q-3 (PE, 2026-10-23): "Por encima se rechaza con 400". ¿422 o 400 para una pregunta de más de 1.000 caracteres? Resuelto (PE, 2026-10-23): 422 para toda la validación, incluida la pregunta de más de 1.000 caracteres; reemplaza el 400 de Q-3 (RFC 9110, comportamiento por defecto de FastAPI con Pydantic). | p. 6 | resolved |

## Coverage

One row per section of the document. A section that requires OCR is never covered.

| Section | Ref | Covered by | Status |
|---|---|---|---|
| S1 | p. 1 | I-4, C-3 | covered |
| S2 | p. 2 | I-1, I-3, I-5, I-6, I-11, C-1, C-2 | covered |
| S3 | p. 3 | I-6, I-11 | covered |
| S4 | p. 4 | I-1, I-11 | covered |
| S5 | p. 5 | I-1, I-2, I-3, I-7, I-8, C-4 | covered |
| S6 | p. 6 | I-2, I-3, I-6, I-9, I-10 | covered |
| S7 | p. 7 | I-10 | covered |
| S8 | p. 8 | I-10 | covered |
