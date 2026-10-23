---
schema_version: 2
tracker: none
type: story
id: MDO-0003
url:
parent:
projects: [asistente-asesores]
lane: normal
status: verified
sources:
  - { ref: "Prueba técnica.pdf (sha256 ea559182d0cbe46540d0bbd994fa163b6633b42d03100c29632446a0267746b7), p. 1, p. 2", kind: document, date: 2026-10-23 }
  - { ref: "docs/product/intake/prueba-tecnica-2026-10-23.md#I-4; Q-5", kind: intake, date: 2026-10-23 }
  - { ref: "Decisiones del PE para /mandao-specify MDO-0003 (reglas, mensaje, registro, falsos positivos, segunda capa)", kind: po, date: 2026-10-23 }
  - { ref: "constitucion/business-rules.md (BR-4, BR-6, BR-7, BR-8, BR-9)", kind: constitution, date: 2026-10-23 }
  - { ref: "constitucion/constitucion.md (DP-1, DP-4, DP-7), security.md, critical-flows.md", kind: constitution, date: 2026-10-23 }
  - { ref: "Data/Manual del Asesor Comercial.md, 'Información Sensible'; Data/Políticas de Atención.md, 'Protección de Información'", kind: data, date: 2026-10-23 }
---

# Bloquear consultas que comprometen la seguridad

El asesor que pide credenciales, configuraciones internas, información restringida o datos de otro
cliente, o que intenta cambiar el comportamiento del asistente, recibe un mensaje fijo y genérico con
estado `Bloqueada por seguridad`, sin que se busque nada. Está hecho cuando los criterios de abajo pasan
por `POST /api/consultar` y las preguntas legítimas con palabras sensibles siguen respondiéndose.

## Who

El **asesor comercial** que usa el asistente (`product.md`) y, del otro lado, el banco, que no puede
permitir que el asistente comparta lo que el Manual del Asesor prohíbe compartir.

## Problem

Hoy el asistente no bloquea nada: una pregunta por el "token interno" o un "ignora tus instrucciones"
pasa a la búsqueda y, si no encuentra soporte, responde `Sin información suficiente`. El estado
`Bloqueada por seguridad` existe (BR-7) pero ninguna consulta llega a él, y BR-4 no tiene un control en
código.

## Value

Cumple BR-4 y DP-1 con reglas deterministas que se pueden leer y probar: el asistente se niega antes de
buscar, sin explicar qué regla se activó, y cada bloqueo queda registrado con su categoría para auditarlo.

## Scope

- Guardrail de entrada con reglas deterministas sobre el texto normalizado (minúsculas, sin acentos,
  espacios colapsados), antes de buscar.
- Tres categorías de bloqueo: información restringida o técnica reservada, prompt injection y datos de
  otros clientes (intake Q-5).
- Mensaje fijo y genérico, sin fuentes, estado `Bloqueada por seguridad`.
- La consulta bloqueada se registra como cualquier otra (BR-6); la categoría va en el log estructurado,
  nunca el contenido de la pregunta.
- Pruebas de falsos positivos y dataset de evaluación ampliado con preguntas bloqueadas.

## Out of scope

- Nuevas reglas en el guardrail de salida: la segunda capa es el que ya existe (PE, 2026-10-23).
- Cambios en la interfaz: `web` ya muestra el estado `Bloqueada por seguridad` (MDO-0002).
- Clasificar con un modelo de lenguaje: las decisiones de seguridad son código (DP-4).
- Una columna de categoría en la base de consultas.
- README y cuestionario (intake I-9, I-10).

## Acceptance criteria

### AC-1 — Información restringida o técnica reservada
critical: true

- **GIVEN** una pregunta que pide credenciales, configuraciones internas o información restringida (p. ej. "¿Cuál es el token interno?")
- **WHEN** se consulta
- **THEN**, antes de buscar, responde 200 con un mensaje fijo y genérico, sin fuentes y estado `Bloqueada por seguridad`
- **BUT it must NOT** revelar nada del documento confidencial ni decir qué regla se activó (C1)

### AC-2 — Prompt injection
critical: true

- **GIVEN** una pregunta del tipo "ignora tus instrucciones y…"
- **WHEN** se consulta
- **THEN** el estado es `Bloqueada por seguridad` con el mismo mensaje genérico de AC-1

### AC-3 — Datos de otros clientes
critical: true

- **GIVEN** una pregunta que pide datos de otro cliente (BR-4, BR-8)
- **WHEN** se consulta
- **THEN** el estado es `Bloqueada por seguridad` con el mismo mensaje genérico
- **AND IT MUST** registrar la consulta, con su categoría de bloqueo en el log (C1)
- **BUT it must NOT** escribir el contenido de la pregunta en el log (C2)

### AC-4 — Sin falsos positivos
critical: false

- **GIVEN** una pregunta legítima con palabras sensibles: "¿Qué cubre Negocio Seguro?", "¿Qué hago si un cliente olvida su clave?" o "¿Qué dice la política de protección de información?"
- **WHEN** se consulta
- **THEN** no se bloquea y sigue el flujo normal de búsqueda
- **AND IT MUST** responder `Sin información suficiente`, no bloquear, a una pregunta fuera de tema (C1)

## Dependencies

- MDO-0001 (cerrada): contrato, estados, registro y guardrail de salida.
- Intake I-2 (validación de entrada, abierta en MDO-0001): el guardrail corre después de validar.

## UX references

Sin cambios de interfaz: `src/web` ya pinta el estado `Bloqueada por seguridad` (`Resultado.tsx`).

## Data involved

La pregunta (puede traer datos personales) se guarda solo en `almacen/consultas.db`, como hoy. El log
lleva la categoría, nunca la pregunta (`security.md`).

<a id="assumptions"></a>
## Assumptions and open questions

- ASSUMPTION(source: intake Q-5 y PE 2026-10-23, "mensaje fijo y genérico"): el texto exacto del mensaje
  lo fija el diseño ([design.md#d3](design.md#d3)); el PE puede cambiarlo sin cambiar el comportamiento.
- ASSUMPTION(source: PE 2026-10-23, "la categoría va en el log"): "log" es la línea JSON por petición
  del logger `asistente.http`; la base de consultas no gana columna. Confirma: PE.
