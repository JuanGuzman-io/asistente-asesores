---
schema_version: 2
tracker: none
type: story
id: MDO-0002
url:
parent:
projects: [web]
lane: normal
status: approved
sources:
  - { ref: "docs/product/intake/prueba-tecnica-2026-10-23.md#I-8 (E-2; C-4; Q-2)", kind: intake, date: 2026-10-23 }
  - { ref: "Prueba técnica.pdf (sha256 ea559182d0cbe46540d0bbd994fa163b6633b42d03100c29632446a0267746b7), p. 5", kind: document, date: 2026-10-23 }
  - { ref: "Decisiones del PE en la sesión /mandao-specify: proyecto web, stack, contrato, EstadoProcesamiento, pruebas, Bloqueada por seguridad, licencias, Playwright, código de referencia", kind: po, date: 2026-10-23 }
  - { ref: "especificaciones/MDO-0001-consultar-la-base-documental-con-fuentes/design.md#contract (rama feat/MDO-0001-…)", kind: spec, date: 2026-10-23 }
  - { ref: "constitucion/ux.md, glossary.md, standards.md#errors, critical-flows.md, architecture.md", kind: constitution, date: 2026-10-23 }
---

# Consultar desde la interfaz

El asesor comercial consulta desde una pantalla local y ve, sin salir de ella, el estado de
procesamiento, la respuesta, sus fuentes y el estado de la respuesta, o un error claro cuando la
consulta falla. Está hecho cuando los dos criterios de abajo pasan en la interfaz.

## Who

El **asesor comercial**, que consulta mientras atiende a un cliente y necesita leer la respuesta y
comprobar su fuente en el momento (`product.md`).

## Problem

Hoy la consulta solo existe como API (`POST /api/consultar`, MDO-0001): el asesor no tiene dónde
escribir la pregunta ni dónde ver la respuesta con sus fuentes, y un error del servicio no le dice nada.

## Value

El asesor usa el asistente sin herramientas técnicas, ve siempre de dónde sale cada respuesta y en
qué estado quedó, y sabe qué hacer cuando algo falla. Es el entregable 6 del PDF (p. 5).

## Scope

- Una pantalla local para escribir la pregunta y enviarla.
- El estado de procesamiento (`inactivo`, `procesando`, `completado`, `error`) mientras se consulta.
- La respuesta, el estado de la respuesta y cada fuente con documento, sección y fragmento.
- Los tres estados de la respuesta, incluido `Bloqueada por seguridad`, aunque el backend aún no lo
  produzca (llega en MDO-0003).
- Errores claros para consultas rechazadas, fallas del servicio y falta de conexión.

## Out of scope

- El backend y su contrato (MDO-0001) y el bloqueo por seguridad (MDO-0003).
- Historial de consultas anteriores, autenticación, despliegue y diseño visual (`ux.md`, `product.md`).
- README y cuestionario (intake I-9, I-10).

## Acceptance criteria

### AC-1 — Realizar consulta y ver la respuesta
critical: true

- **GIVEN** la interfaz local abierta y el servicio de consultas disponible
- **WHEN** el asesor escribe una pregunta y la envía
- **THEN** ve el estado de procesamiento mientras espera y luego la respuesta, sus fuentes (documento, sección y fragmento) y el estado de la respuesta
- **BUT it must NOT** enviar otra consulta mientras la anterior está en procesamiento (C1)
- **AND IT MUST** mostrar el estado de la respuesta (`Exitosa`, `Sin información suficiente` o `Bloqueada por seguridad`) visible y distinguible, también cuando no hay fuentes (C2)
- **BUT it must NOT** interpretar como HTML ni como enlace el texto de la respuesta o de las fuentes (C3)

### AC-2 — Ver errores
critical: false

- **GIVEN** una consulta rechazada por el servicio (pregunta vacía, demasiado larga o inválida), un error del servicio o sin conexión con él
- **WHEN** llega la respuesta o falla la conexión
- **THEN** la interfaz muestra un error claro en español y, si el servicio lo envía, su código de referencia
- **BUT it must NOT** mostrar detalles técnicos: trazas, rutas ni el cuerpo crudo de la respuesta (C1)
- **AND IT MUST** conservar la pregunta escrita para que el asesor pueda corregirla o reintentar (C2)

## Dependencies

- MDO-0001: el contrato de `POST /api/consultar` ([design.md#contract](../MDO-0001-consultar-la-base-documental-con-fuentes/design.md) en su rama). Las pruebas usan un backend simulado con ese contrato; las de punta a punta necesitan MDO-0001 en `main`.

## UX references

Ninguna: HTML nativo, sin librería de UI; el diseño visual no se evalúa (`ux.md`). Mock declinado
por el PE (2026-10-23).

## Data involved

Solo la pregunta del asesor, que se envía al servicio y no se guarda en el navegador; puede traer
datos personales que escriba el asesor (`security.md`).

<a id="assumptions"></a>
## Assumptions and open questions

- `CONFLICT` resuelto (a: MDO-0001 `story.md` "seguridad (MDO-0002) y la interfaz (MDO-0003)"; b: PE 2026-10-23 "Esta spec (MDO-0002) es el frontend… llega en MDO-0003"; decides: PE, resolved): MDO-0002 es la interfaz y MDO-0003 la seguridad. Las referencias de MDO-0001 se corrigen en esa spec, no en esta rama.
- ASSUMPTION(source: critical-flows.md, "Consulta respondida con fuentes y registrada"): AC-1 es el camino del asesor por ese flujo crítico, por eso `critical: true` y lleva prueba de punta a punta.
