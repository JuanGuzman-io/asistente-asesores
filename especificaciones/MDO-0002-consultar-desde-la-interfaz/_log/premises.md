# Premises

## P1 — run

- Claim: El contrato aprobado de MDO-0001 es el que consume esta spec
- Command: `sh especificaciones/MDO-0002-consultar-desde-la-interfaz/_log/premises/probes/p1_contrato.sh` (from the worktree root)
- Ran at: 2026-10-23T16:25:30.064Z on 440e5cc
- Exit: 0

```
## Contract
`POST /api/consultar`, `Content-Type: application/json`, cuerpo ≤ 16 KB.
- Petición: `{"pregunta": string}` (1–1.000 caracteres tras `strip()`).
- 200: `{"respuesta": string, "fuentes": [{"documento": string, "seccion": string, "fragmento": string}], "estado": "Exitosa" | "Sin información suficiente" | "Bloqueada por seguridad"}`.
- 413 / 415 / 422 / 500: `application/problem+json` con `type`, `title`, `status`, `detail`, `requestId`.
- Todas las respuestas llevan `X-Request-Id`.
MDO-0003 (interfaz) consume este contrato; MDO-0002 solo agrega el estado `Bloqueada por seguridad`.
## Risks and risk tags
```

## P2 — run

- Claim: `typescript-eslint` 8.72.0 no admite TypeScript 7
- Command: `sh especificaciones/MDO-0002-consultar-desde-la-interfaz/_log/premises/probes/p2_peer.sh` (from the worktree root)
- Ran at: 2026-10-23T16:25:30.791Z on 440e5cc
- Exit: 0

```
{
  "eslint": "^8.57.0 || ^9.0.0 || ^10.0.0",
  "typescript": ">=4.8.4 <6.1.0"
}
npm notice
npm notice New major version of npm available! 10.9.8 -> 12.2.1
npm notice Changelog: https://github.com/npm/cli/releases/tag/v12.2.1
npm notice To update run: npm install -g npm@12.2.1
npm notice
```

## P3 — run

- Claim: El Node local cumple los motores de Vite, Vitest y jsdom
- Command: `sh especificaciones/MDO-0002-consultar-desde-la-interfaz/_log/premises/probes/p3_engines.sh` (from the worktree root)
- Ran at: 2026-10-23T16:25:32.966Z on 440e5cc
- Exit: 0

```
v22.23.2
^20.19.0 || >=22.12.0
npm notice
npm notice New major version of npm available! 10.9.8 -> 12.2.1
npm notice Changelog: https://github.com/npm/cli/releases/tag/v12.2.1
npm notice To update run: npm install -g npm@12.2.1
npm notice
^22.12.0 || ^24.0.0 || >=26.0.0
^22.22.2 || ^24.15.0 || >=26.0.0
OK: cumple ^22.22.2
```
