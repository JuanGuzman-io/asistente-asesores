---
schema_version: 1
level: workspace
status: approved
last_reviewed: 2026-10-23
---

# Critical flows

Flows that require e2e coverage and performance budgets. AC touching them carry `critical: true`.

| Flow | Projects | E2E suite | Budget (see performance.md) |
|---|---|---|---|
| Consulta respondida con fuentes y registrada | asistente-asesores | OPEN (por crear) | `POST /api/consultar` p95 |
| Consulta bloqueada por seguridad (información restringida o prompt injection) | asistente-asesores | OPEN (por crear) | `POST /api/consultar` p95 |
