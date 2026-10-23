---
schema_version: 1
level: workspace
status: approved
last_reviewed: 2026-10-23
security_scanning:
  secrets:
    local: []
    ci: []
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
    ci: []
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
Propuesta: GitHub Actions en cada PR con lint, typecheck, pruebas y escaneo de secretos (herramientas
gratuitas). Aún no existe.

## Security scanning
`security_scanning` in this document's frontmatter records secrets and SAST independently.
`local`, `ci` and `provider` list evidence detected from project gates, CI files and provider APIs;
`declared` uses the same locations for tools the user reports manually and is not presented as
detected evidence. `unknown` names sources that could not be verified. Empty lists mean `none` only
when all corresponding `checked` locations are true; otherwise the state is `unknown`.

Estado detectado (2026-10-23, `run security-scanning`): sin escáner de secretos ni SAST local o en CI;
el del proveedor no es verificable desde el repositorio → `unknown`.

## Cloud and services
Gemini API (Google), activada con `GEMINI_API_KEY`; sin clave, modo extractivo local
(`model-registry.md`). El modelo de embeddings se descarga una vez y luego corre sin red.

## Observability
Log JSON por consulta (`requestId`, `estado`, `latenciaMs`, número de fuentes) y la tabla de consultas
persistida. Métricas a vigilar: proporción por estado, latencia p95, bloqueos por seguridad.
