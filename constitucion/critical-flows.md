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
| Consulta respondida con fuentes y registrada | asistente-asesores, web | `tests/server/e2e/` (`test_flujo_consulta.py`, `test_arranque_indice.py`, `test_respaldo_e2e.py`; MDO-0001); desde la interfaz, `tests/web/e2e/consultar.spec.ts` (MDO-0002) | `POST /api/consultar` p95 |
| Consulta bloqueada por seguridad (información restringida o prompt injection) | asistente-asesores | OPEN (por crear) | `POST /api/consultar` p95 |
