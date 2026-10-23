---
schema_version: 2
tracker: none
type: story
id: MDO-0001
url:
parent:
projects: [asistente-asesores]
lane: normal
status: in-progress
sources:
  - { ref: "Prueba técnica.pdf (sha256 ea559182d0cbe46540d0bbd994fa163b6633b42d03100c29632446a0267746b7), p. 2, p. 3, p. 4, p. 5, p. 6", kind: document, date: 2026-10-23 }
  - { ref: "docs/product/intake/prueba-tecnica-2026-10-23.md#I-6, I-1, I-2, I-3, I-5, I-7; Q-2, Q-3, Q-4, Q-6", kind: intake, date: 2026-10-23 }
  - { ref: "Respuestas del PE: alcance, soporte parcial y formato de fuente (sesión /mandao-story)", kind: po, date: 2026-10-23 }
  - { ref: "constitucion/business-rules.md (BR-1, BR-2, BR-3, BR-6, BR-7, BR-9)", kind: constitution, date: 2026-10-23 }
  - { ref: "constitucion/standards.md#errors (códigos de error, PE)", kind: constitution, date: 2026-10-23 }
  - { ref: "constitucion/glossary.md, product.md, critical-flows.md, performance.md, security.md, standards.md, architecture.md, model-registry.md", kind: constitution, date: 2026-10-23 }
  - { ref: "Data/ (seis archivos; Productos de Crédito.md, 'Crédito Productivo Impulso')", kind: data, date: 2026-10-23 }
---

# Consultar la base documental con fuentes

El asesor comercial pregunta por `POST /api/consultar` y recibe una respuesta construida solo con la
base documental oficial, con sus fuentes, o el mensaje fijo de falta de información; cada consulta queda
registrada. Está hecho cuando los criterios de abajo pasan por la API, sin interfaz.

## Who

El **asesor comercial**, que consulta sobre productos de crédito, microseguros, procedimientos operativos
y políticas internas mientras atiende a un cliente (`product.md`, BR-9).

## Problem

Hoy el asesor busca la respuesta a mano en varios documentos y puede dar información desactualizada o
inventada sin poder decir de dónde la sacó, lo que contradice BR-1 y BR-2.

## Value

Respuestas rápidas, verificables y sustentadas solo en documentación oficial, con la fuente a la vista
para que el asesor pueda comprobarla. Es el núcleo que necesitan la seguridad (MDO-0002) y la interfaz
(MDO-0003).

## Scope

Se entrega en tres partes, en este orden:

1. **Base documental** (intake I-6): los documentos oficiales de `Data/` quedan consultables, sin la
   información restringida y sin duplicados.
2. **Consulta** (I-1, I-2, I-3, I-5): respuesta con fuentes, validación de la pregunta, mensaje fijo sin
   información y registro de cada consulta.
3. **Errores** (I-7): errores controlados y respaldo extractivo cuando el modelo falla.

- Contrato `{ "pregunta" }` → `{ "respuesta", "fuentes", "estado" }`; los tres estados de negocio
  responden 200 (Q-2).
- Cada fuente muestra documento, sección y el fragmento usado.

## Out of scope

- Bloqueo por seguridad (información restringida, prompt injection, datos de otros clientes): MDO-0002.
- Interfaz para consultar: MDO-0003.
- README y cuestionario (intake I-9, I-10).
- Autenticación, despliegue y edición de documentos desde la aplicación (`product.md`).

## Acceptance criteria

### AC-1 — Documentos oficiales consultables
critical: true

- **GIVEN** los seis archivos de `Data/`
- **WHEN** se prepara la base documental
- **THEN** los cinco documentos oficiales, incluido `Políticas de Atención.md`, quedan consultables
- **BUT it must NOT** quedar consultable ningún contenido de `Información restringida.md` (C1)

### AC-2 — Documentos duplicados
critical: false

- **GIVEN** dos documentos con el mismo contenido en la base documental
- **WHEN** se prepara la base y luego se hace una consulta que ese contenido responde
- **THEN** el contenido se considera una sola vez
- **BUT it must NOT** aparecer la misma fuente repetida en la respuesta (C1)

### AC-3 — Consulta válida con soporte documental
critical: true

- **GIVEN** la base documental con `Productos de Crédito.md`
- **WHEN** el asesor envía `{"pregunta": "¿Cuál es el monto máximo del Crédito Productivo Impulso?"}` a `POST /api/consultar`
- **THEN** recibe 200 con `respuesta`, `fuentes` y `estado` `Exitosa`, y la respuesta trae el monto máximo que dice el documento
- **AND IT MUST** citar al menos una fuente (C1)

### AC-4 — Solo información encontrada
critical: true

- **GIVEN** una consulta con soporte documental
- **WHEN** el asistente responde
- **THEN** todo dato de la respuesta está en alguno de los fragmentos citados
- **BUT it must NOT** inferir, completar ni agregar datos que no estén en la base documental (C1)

### AC-5 — Soporte parcial
critical: true

- **GIVEN** una pregunta con dos partes, de las que la base documental solo responde una (p. ej. monto y una tasa que no existe en los documentos), y el modelo de redacción configurado
- **WHEN** se consulta
- **THEN** la respuesta contesta solo la parte con soporte, la cita y dice explícitamente qué parte no está en la base documental (p. ej. "No encontré información sobre la tasa"), con estado `Exitosa`
- **BUT it must NOT** completar ni estimar la parte faltante (C1)
- **AND IT MUST**, sin modelo, empezar con "Esto es lo que encontré en la base documental:" y no afirmar que cubre toda la pregunta ([C-1](requirements.md#c-1)) (C2)

### AC-6 — Contenido de cada fuente
critical: true

- **GIVEN** una respuesta `Exitosa`
- **WHEN** el asesor revisa `fuentes`
- **THEN** cada fuente indica el documento, la sección y el fragmento usado (p. ej. "Productos de Crédito > Crédito Productivo Impulso" y el texto de esa sección)
- **AND IT MUST** corresponder cada fuente a un fragmento usado en la respuesta (C1)

### AC-7 — Pregunta vacía o cuerpo inválido
critical: false

- **GIVEN** una pregunta vacía, solo con espacios, o un cuerpo que no trae `pregunta` como texto
- **WHEN** se envía a `POST /api/consultar`
- **THEN** la API responde 422 en formato RFC 9457, con `requestId` y un mensaje claro
- **BUT it must NOT** consultar documentos ni registrar la consulta (C1)

### AC-8 — Caracteres especiales
critical: false

- **GIVEN** una pregunta con tildes, eñes, signos de apertura, comillas y emojis
- **WHEN** se envía
- **THEN** se procesa sin error y responde según la base documental
- **BUT it must NOT** fallar la búsqueda por esos caracteres (C1)

### AC-9 — Consulta extensa
critical: false

- **GIVEN** una pregunta de 1.001 caracteres Unicode después de quitar los espacios al inicio y al final
- **WHEN** se envía
- **THEN** la API responde 422 en formato RFC 9457 con un mensaje claro sobre el límite
- **AND IT MUST** aceptar y procesar una pregunta de exactamente 1.000 caracteres (C1)
- **BUT it must NOT** recortar, consultar ni registrar la pregunta rechazada (C2)

### AC-10 — Cuerpo o tipo de contenido no admitidos
critical: false

- **GIVEN** un cuerpo mayor a 16 KB, o un tipo de contenido distinto de JSON
- **WHEN** se envía
- **THEN** la API responde 413 o 415 respectivamente, en formato RFC 9457 con `requestId`

### AC-11 — Sin soporte documental
critical: true

- **GIVEN** una pregunta de los cuatro temas que la base documental no responde
- **WHEN** se consulta
- **THEN** responde 200 con la respuesta exacta "No tengo información suficiente para responder.", sin fuentes y estado `Sin información suficiente`

### AC-12 — Base documental vacía
critical: false

- **GIVEN** una base documental sin documentos consultables
- **WHEN** se consulta
- **THEN** responde 200 con el mismo mensaje fijo y estado `Sin información suficiente`
- **BUT it must NOT** fallar ni responder con error (C1)

### AC-13 — Pregunta fuera de tema
critical: false

- **GIVEN** una pregunta ajena a los cuatro temas (BR-9), p. ej. sobre el clima
- **WHEN** se consulta
- **THEN** responde con el mensaje fijo y estado `Sin información suficiente`
- **BUT it must NOT** quedar `Bloqueada por seguridad` (C1)

### AC-14 — Registro de cada consulta
critical: true

- **GIVEN** una consulta procesada con cualquier estado
- **WHEN** termina
- **THEN** queda almacenada con la pregunta, la fecha y hora, la respuesta generada, las fuentes utilizadas y el estado
- **BUT it must NOT** registrarse una pregunta rechazada por validación (AC-7, AC-9, AC-10) (C1)

### AC-15 — Error inesperado
critical: false

- **GIVEN** una falla inesperada al buscar o al guardar
- **WHEN** se consulta
- **THEN** la API responde 500 en formato RFC 9457 con `requestId` y un mensaje genérico
- **BUT it must NOT** exponer detalles internos, rutas, trazas ni datos sensibles (C1)

### AC-16 — Falla del modelo
critical: true

- **GIVEN** que el modelo de redacción falla, no responde o no está configurado
- **WHEN** se consulta una pregunta con soporte documental
- **THEN** responde 200 con una respuesta extractiva (los fragmentos y sus fuentes) y estado `Exitosa`

## Dependencies

- Constitución aprobada: contrato, estados, mensaje fijo y límites (`business-rules.md`, `performance.md`).
- El modelo de redacción es opcional: sin él la solución funciona en modo extractivo (`model-registry.md`).
- MDO-0002 (seguridad) y MDO-0003 (interfaz) dependen de esta spec.

## UX references

Ninguna: esta spec no tiene interfaz (la interfaz es MDO-0003).

## Data involved

- Base documental: los cinco documentos oficiales de `Data/` (clase interna, `security.md`); se excluye
  `Información restringida.md` (confidencial).
- Registro de consultas: pregunta, fecha y hora, respuesta, fuentes y estado (BR-6). La pregunta puede
  traer datos personales que escriba el asesor: se guarda solo en la base local de consultas, nunca en
  logs (`security.md`).

<a id="assumptions"></a>
## Assumptions and open questions

- Duplicados y conteo de caracteres: resueltos en [requirements.md#c-2](requirements.md#c-2); modo extractivo de AC-5: [C-1](requirements.md#c-1).
- ASSUMPTION(source: intake I-5 AC-1, Q-5): el registro de consultas `Bloqueada por seguridad` se verifica en MDO-0002; aquí AC-14 cubre los estados `Exitosa` y `Sin información suficiente`.
