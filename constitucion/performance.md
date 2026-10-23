---
schema_version: 1
level: workspace
status: approved
last_reviewed: 2026-10-23
---

# Performance

## Budgets
| Flow / route | Metric | Budget | Measured with |
|---|---|---|---|
| `POST /api/consultar` (modo extractivo) | p95 latencia local | ≤ 300 ms | prueba de carga local (locust) |
| `POST /api/consultar` (con Gemini) | p95 latencia | ≤ 3 s | misma prueba, con `GEMINI_API_KEY` |
| Arranque del servidor | indexado de `Data/` con embeddings ya calculados | ≤ 2 s | log de arranque |
| Primer arranque | descarga del modelo de embeddings y cálculo inicial | sin presupuesto (una vez) | log de arranque |
| Pregunta | longitud máxima | 1.000 caracteres | validación de entrada |

ASSUMPTION: presupuestos iniciales para ejecución local; se ajustan con la primera medición.

## Measurement protocol
Build de producción, máquina local, N ≥ 5 corridas con mediana y dispersión, base documental de `Data/`
más los registros que se agreguen para robustecer la prueba.
