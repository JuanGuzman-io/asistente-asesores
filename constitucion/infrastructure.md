---
schema_version: 1
level: workspace
status: approved
last_reviewed: 2026-10-23
security_scanning:
  secrets:
    local: []
    ci:
      - detect-secrets (.github/workflows/ci.yml, job backend)
    provider: []
    declared:
      local: []
      ci: []
      provider: []
    unknown:
      - provider-managed scanning is not inspectable from repository files
    checked:
      local: true
      ci: true
      provider: false
  sast:
    local: []
    ci:
      - bandit (.github/workflows/ci.yml, job backend)
    provider: []
    declared:
      local: []
      ci: []
      provider: []
    unknown:
      - provider-managed scanning is not inspectable from repository files
    checked:
      local: true
      ci: true
      provider: false
---

# Infrastructure

## Branching
`feature-branch` (decisión 2026-10-23). Base y destino de PR: `main`; producción: `main`; prefijos
`feat/`, `fix/`, `hotfix/`; `main` protegida.

## Environments
Solo local (PDF, entregable 6). Sin despliegue.

## CI/CD
GitHub Actions (`.github/workflows/ci.yml`, PE 2026-10-23) en cada PR y en cada push a `main`, con las
acciones fijadas por SHA. Tres jobs:

- `backend`: `uv sync` y los gates de `.mandao/config.yml`: format, lint, typecheck, test (sin red, en
  un namespace de red vacío), secrets (detect-secrets), sast (bandit) y audit (pip-audit).
- `evals`: `uv run pytest -m eval`, con el modelo de embeddings en caché (`FASTEMBED_CACHE_PATH`).
- `frontend`: solo si la rama tiene `src/web`. `npm ci`, sus gates (format, lint, typecheck, test,
  build, `npm audit`) y las e2e de Playwright contra el backend levantado con un worker y sin clave de
  Gemini.

## Security scanning
`security_scanning` in this document's frontmatter records secrets and SAST independently.
`local`, `ci` and `provider` list evidence detected from project gates, CI files and provider APIs;
`declared` uses the same locations for tools the user reports manually and is not presented as
detected evidence. `unknown` names sources that could not be verified. Empty lists mean `none` only
when all corresponding `checked` locations are true; otherwise the state is `unknown`.

Estado (2026-10-23): en CI corren detect-secrets (secretos) y bandit (SAST) en el job `backend`; el
escaneo del proveedor no es verificable desde el repositorio → `unknown`.

## Cloud and services
Gemini API (Google), activada con `GEMINI_API_KEY`; sin clave, modo extractivo local
(`model-registry.md`). El modelo de embeddings se descarga una vez y luego corre sin red.

## Observability
Log JSON por consulta (`requestId`, `estado`, `latenciaMs`, número de fuentes) y la tabla de consultas
persistida. Métricas a vigilar: proporción por estado, latencia p95, bloqueos por seguridad.
