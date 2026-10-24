# Plan — MDO-0003 Bloquear consultas que comprometen la seguridad

Índice del entregable "plan" de la prueba técnica. El contenido vive en los archivos de Mandao; aquí solo
se indica dónde está cada punto.

| Punto | Dónde está |
|---|---|
| Arquitectura | [constitucion/architecture.md](../../constitucion/architecture.md); [design.md: Decisions](design.md#decisions) (D1 a D6) y [Principle check](design.md#principle-check) |
| Componentes | [design.md: Changes by project and module](design.md#changes-by-project-and-module) y [Model and prompts](design.md#model-and-prompts); guía del módulo en [src/server/AGENTS.md](../../src/server/AGENTS.md) |
| Reglas del guardrail | [design.md: D2](design.md#d2) (familias, orden y excepciones) y [D4](design.md#d4) (normalización) |
| Estrategia de pruebas | [design.md: Principle check](design.md#principle-check) (DP-3, TDD) y [Data writes (ACID)](design.md#data-writes-acid); [requirements.md: Eval thresholds](requirements.md#eval-thresholds); niveles de prueba por tarea en [tasks.md: Details](tasks.md#details); resultado en [verify-report.md](verify-report.md) |
| Cómo probarlo | [quickstart.md](quickstart.md) |
