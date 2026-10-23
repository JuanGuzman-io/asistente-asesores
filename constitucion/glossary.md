---
schema_version: 1
level: workspace
status: approved
last_synced: 2026-10-23
---

# Glossary

Business language ↔ names in code. Names that contradict this glossary are blocking in review.

| Business term | Code name(s) | Definition | Source |
|---|---|---|---|
| Asesor comercial | `asesor` | Usuario que hace consultas al asistente. | PDF p. 2 |
| Consulta | `Consulta`, `pregunta` | Pregunta de un asesor y su registro (fecha y hora, respuesta, fuentes, estado). | PDF p. 2 |
| Respuesta | `respuesta` | Texto que responde la consulta usando solo información encontrada. | PDF p. 5 |
| Fuente | `Fuente`, `fuentes` | Documento, sección y fragmento de `Data/` que sustentan la respuesta. | PDF p. 5; Política de Citas; PE 2026-10-23 (MDO-0001) |
| Estado de la respuesta | `Estado`: `EXITOSA`, `SIN_INFORMACION`, `BLOQUEADA` | Exitosa, Sin información suficiente, Bloqueada por seguridad. | PDF p. 2 |
| Procesamiento | — | Estado de la interfaz mientras una consulta está en curso (cargando, listo, error de red). No es el estado de la respuesta, que viene de la API. | PDF p. 5 |
| Base documental | `BaseDocumental`, `Data/` | Documentos oficiales que el asistente puede consultar. | PDF p. 2-3 |
| Información restringida | `confidencial` | Información que ningún asistente debe exponer; no se indexa. | Información restringida.md |
| Escalamiento | `escalar` | Detener la respuesta, escalar el caso y registrar el evento. | Políticas de Atención |
| PQR | — | Peticiones, quejas y reclamos (tiempo objetivo: 5 días hábiles). | Procedimientos Operativos |
| Microseguro | — | Seguro de bajo costo del portafolio (Vida Protegida, Accidente Personal Esencial, Negocio Seguro). | Portafolio de Microseguros |
