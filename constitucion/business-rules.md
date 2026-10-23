---
schema_version: 1
level: workspace
status: approved
last_synced: 2026-10-23
owner: PO
---

# Business rules

Every rule has a source and a date. A rule without a source is an `ASSUMPTION`; contradictory sources
are a `CONFLICT` decided by the PO.

| ID | Rule | Implemented in | Source | Date | Status |
|---|---|---|---|---|---|
| BR-1 | Toda respuesta debe estar sustentada en documentación oficial. | — | Políticas de Atención, "Transparencia"; PDF p. 5 | 2026-10-23 | documented only |
| BR-2 | Toda respuesta generada debe indicar la fuente utilizada. | — | Políticas de Atención, "Política de Citas"; PDF p. 5 | 2026-10-23 | documented only |
| BR-3 | Sin soporte documental, el asistente responde con un mensaje fijo de falta de información. | — | PDF p. 5: "No tengo información suficiente para responder."; Manual del Asesor, "Casos Especiales": "No cuento con información suficiente para responder esa consulta." | 2026-10-23 | documented only — CONFLICT resolved 2026-10-23: se usa la frase del PDF, contrato de la evaluación |
| BR-4 | Nunca se comparte información de otros clientes, configuraciones internas, credenciales ni información tecnológica reservada. | — | Manual del Asesor, "Información Sensible"; Información restringida.md | 2026-10-23 | documented only |
| BR-5 | Ante incertidumbre: detener la respuesta, escalar el caso y registrar el evento. | — | Políticas de Atención, "Política de Escalamiento" | 2026-10-23 | documented only |
| BR-6 | Cada consulta se almacena con pregunta, fecha y hora, respuesta, fuentes y estado. | — | PDF p. 2 | 2026-10-23 | documented only |
| BR-7 | Los estados posibles son `Exitosa`, `Sin información suficiente` y `Bloqueada por seguridad`. | — | PDF p. 2 | 2026-10-23 | documented only |
| BR-8 | La información de clientes solo la consulta personal autorizado. | — | Políticas de Atención, "Protección de Información" | 2026-10-23 | documented only |
| BR-9 | El asistente solo atiende cuatro temas: productos de crédito, microseguros, procedimientos operativos y políticas internas. Una pregunta fuera de ellos no tiene soporte documental: es `Sin información suficiente`, no se bloquea. | — | PDF p. 2; intake Q-5 (PE, 2026-10-23) | 2026-10-23 | documented only |

ASSUMPTION(source: BR-5): en el asistente, "escalar" se traduce en responder `Sin información suficiente`
y registrar el evento; no existe un canal de escalamiento al que enviar el caso.
