---
schema_version: 1
level: workspace
status: approved
last_synced: 2026-10-23
owner: PO
---

# Product

Fuente: *Prueba técnica — Desarrollador de IA* (PDF, 8 páginas, leído 2026-10-23) y la base documental
de `Data/`. No hay código todavía: las capacidades están planeadas, sin evidencia en código.

## Vision
Un asistente interno que responde a los asesores comerciales, con información oficial y citando su
fuente, consultas sobre productos de crédito, microseguros, procedimientos operativos y políticas internas.

## Users and roles
- **Asesor comercial:** hace consultas y recibe respuestas con sus fuentes.
- **Responsable de la base documental:** mantiene los documentos de `Data/`. ASSUMPTION: sin interfaz;
  edita los archivos.

## Scope
- **Dentro:** consultas en lenguaje natural; respuesta solo con información encontrada; citas de
  fuentes; registro de cada consulta con su estado; frontend local.
- **Fuera:** autenticación, despliegue, gestión de clientes, edición de documentos desde la interfaz.

## Capability map

| Capability | Evidence in code | Documented in | Status |
|---|---|---|---|
| Responder consultas con fuentes | — | PDF p. 2, p. 5 | planned |
| Indicar falta de información | — | PDF p. 5; Manual del Asesor, "Casos Especiales" | planned (frase del PDF, ver BR-3) |
| Bloquear consultas sobre información restringida | — | PDF p. 2; Información restringida.md | planned |
| Registrar consultas (pregunta, fecha y hora, respuesta, fuentes, estado) | — | PDF p. 2 | planned |
| Frontend para consultar y ver respuesta, fuentes, errores y estado | — | PDF p. 5 | planned |
