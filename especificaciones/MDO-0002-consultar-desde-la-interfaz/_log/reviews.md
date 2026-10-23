# Reviews

## T1 — attempt 1

VERDICT: FAIL

Model identity: my instructions say not to state which model I am. Mandao records the reviewer from what it invoked.

T1 fails on one thing. `vite.config.ts` lets the dev server serve files from the whole repository, which can expose `Data/Información restringida.md` (F1). Everything else holds. The scenarios, the client contract, the red evidence, the licences and the audit are all fine. Once F1 is fixed I would expect a PASS on attempt 2.

## Summary of checks

1. **Spec conformance (FR-3, D3, S-3.1 to S-3.4/C1, AC-2/C1): met.**
   - `consultar()` never throws and follows the FR-3 table: 422 shows the `detail` or "Revisa…", 413 shows "demasiado larga", any other code or a body that breaks the contract shows the generic message, a network failure shows the connection message, and a timeout shows the timeout message.
   - `requestId` is only passed through when it is a string. A 200 is checked against the three `estado` values and the shape of `fuentes`.
   - No received body, stack trace or field name gets into an error result.
   - D2 (relative `/api/consultar` with the proxy and `API_URL`), D6 (six gates in `.mandao/config.yml`; the `asistente-asesores` gates are unchanged) and D7 (exact pinned versions) are met.
2. **Tests: present and meaningful.** `tests/web/api.test.ts` covers every listed scenario, plus 413, the 422 without `detail` case, broken `fuentes`, a 200 that is not JSON, and a 500 `problem+json` that does not leak its `detail`. Each test uses a mocked `fetch` and an injected timeout. No test cases were removed.
3. **TDD: met.** `execution.md` records a RED run (`npx vitest run tests/web/api.test.ts` exited 1) before the implementation. `redTests.changed` is empty.
4. **Licences: met under the PE decisions of 2026-10-23.** The report shows MIT 181, Apache-2.0 21, ISC 11, BSD-2-Clause 8, BSD-3-Clause 3, MIT-0 2, MPL-2.0 2, BlueOak-1.0.0 2, CC-BY-4.0 1 and CC0-1.0 1. The single `UNLICENSED` entry is `web@0.0.0`, the project itself (`private: true`). The direct dependencies are MIT or Apache-2.0.
5. **npm audit: met.** It reported "found 0 vulnerabilities" both times.
6. **`main.tsx` in T1's files:** the PE approved it. The minimal mount is fine.
7. **`src/web/.prettierignore` outside the declared files: justified.** `src/web/AGENTS.md` and `src/web/CLAUDE.md` exist and Mandao regenerates them. `prettier --check .` would fail the format gate on them, and running with `--write` would rewrite them. `*.md` is wider than needed (a future README would not be formatted), so it is advisory (F4). The file should be added to T1's recorded files.
8. **Gates:** I only have the Leader's results. All seven passed (scan-markers, format, lint, typecheck, test, build, audit). I claim nothing beyond that.
9. **Module boundaries:** fine. `api.ts` holds only the HTTP client and the screen is not touched.

## Findings (JSON)

```json
{"version":1,"findings":[
{"id":"F1","status":"open","severity":"medium","lens":"security","title":"The Vite dev server is allowed to serve the whole repository, including the confidential Data/Información restringida.md","file":"src/web/vite.config.ts","line":9,"evidence":"`server: { fs: { allow: [\"../..\"] } }` puts the repository root on Vite's allow-list, so any file in it can be fetched through `/@fs/<absolute path>`. Vite's default `fs.deny` covers `.env`, `.env.*`, certificates and `.git`, but not `Data/*.md`. The module index in AGENTS.md says `Información restringida.md` 'nunca se indexa ni se expone', and DP-1 (seguridad por defecto) applies. Vitest runs the tests in Node with jsdom, so it does not need this to load ../../tests/web. ASSUMPTION: I am relying on Vite's documented `server.fs` behaviour and could not run the server. Fix: remove `fs.allow`, or narrow it to `[\".\", \"../../tests/web\"]`, and add `Data/**` to `fs.deny`. Blocking: the diff introduces it, the task has the security risk tag, and the fix is one line in a declared file."},
{"id":"F2","status":"open","severity":"medium","lens":"core","title":"The format and lint gates do not cover tests/web","file":"src/web/package.json","line":10,"evidence":"`prettier --check .` and `eslint .` run from src/web, so ../../tests/web is never formatted or linted; only `tsc` includes it. `tests/web/api.test.ts` has lines over the 110-column printWidth (the stubFetch `new Response(...)` lines in S-2.1 base, S-3.4/C1 and the HTML-body S-3.4 case). Its `describe(\"consultar: sin detalles técnicos…\")` callback is about 70 lines, over the 50-line max-lines-per-function in standards.md. Advisory, because standards.md does not say whether its thresholds apply to tests. Recommend adding ../../tests/web to both gates, or deciding explicitly that tests are excluded, before T2 and T3 copy this pattern. If they are added, split the tests rather than delete cases."},
{"id":"F3","status":"open","severity":"medium","lens":"core","title":"src/web/AGENTS.md does not describe the new module","file":"src/web/AGENTS.md","line":12,"evidence":"Only the Mandao-managed block exists. Nothing outside the markers gives the module's purpose, the npm scripts and gates, the place of the tests (tests/web), the API_URL proxy, or api.ts as the client exemplar. The file is not in T1's declared files, so this is not held against the Implementer. The Leader should add it at T1 or at close."},
{"id":"F4","status":"open","severity":"low","lens":"core","title":".prettierignore is outside the declared files and its `*.md` is broader than needed","file":"src/web/.prettierignore","line":4,"evidence":"Justified: AGENTS.md and CLAUDE.md are Mandao-managed. Narrow the rule to `AGENTS.md` and `CLAUDE.md`, and record the file in T1's files."},
{"id":"F5","status":"open","severity":"low","lens":"core","title":"The licence exception in the spec and in standards.md does not list MIT-0 and CC0-1.0","file":"especificaciones/MDO-0002-consultar-desde-la-interfaz/spec.md","line":245,"evidence":"The PE approved MIT-0 and CC0-1.0 on 2026-10-23, and the report contains @csstools/* (MIT-0) and mdn-data (CC0-1.0). D7 and the Justified exceptions row list only MPL-2.0, PSF-2.0, ISC, BlueOak-1.0.0 and CC-BY-4.0. standards.md#dependencies still says only MIT, Apache-2.0 and BSD (already planned for close)."},
{"id":"F6","status":"open","severity":"low","lens":"security","title":"A valid 200 passes unknown fields through in `resultado`","file":"src/web/src/api.ts","line":79,"evidence":"`{ tipo: \"ok\", resultado: cuerpo }` returns the whole parsed body, extra fields included. Advisory: build `{ respuesta, fuentes: fuentes.map(...), estado }` so nothing outside the contract reaches the UI."},
{"id":"F7","status":"open","severity":"low","lens":"core","title":"A caller's signal replaces the 30 s timeout, and AbortError is reported as a timeout","file":"src/web/src/api.ts","line":90,"evidence":"`opciones.signal ?? AbortSignal.timeout(TIEMPO_LIMITE_MS)`: if T3 passes its own signal to cancel, the 30 s limit is lost and a user cancel shows 'tardó demasiado'. Advisory: combine them with `AbortSignal.any([...])`. No test covers the default 30 s timeout (fake timers would)."}
]}
```

## T1 — attempt 2

VERDICT: PASS

T1 attempt 2 passes. F1, F3 and F4 are fixed in the diff. F2, F5, F6 and F7 are still open but advisory, and none of them blocks. I checked the attempt-2 pack. Only `vite.config.ts`, `.prettierignore` and `src/web/AGENTS.md` changed. The manifest hashes for `api.ts` and `tests/web/api.test.ts` match attempt 1. All seven gates pass. I have no shell, so I did not reproduce the curl results; I accepted them as reported by the Implementer.

## What changed

1. **F1, resolved.** `server.fs.allow` is now `[".", "../../tests/web"]`, so the dev server can only serve `src/web` and `tests/web`. `Data/` and the repository root are outside both.
   - `server.fs.deny` re-declares Vite's default entries (`.env`, `.env.*`, `*.{crt,pem}`, `**/.git/**`). This matters because setting `deny` replaces the defaults instead of adding to them. It also adds `**/Data/**` as a second layer.
   - The reported curl results fit this config. `/@fs/.../Data/Información restringida.md` returned 403, also with `?raw`. Another `Data/` file and the root `CLAUDE.md` also returned 403. `/Data/` returned only the SPA `index.html` fallback, which is not file content.
   - Keeping `../../tests/web` in the allow-list is justified: by the Implementer's report, Vitest could not collect the tests without it.
2. **F3, resolved.** `src/web/AGENTS.md` now has a Spanish module section outside the Mandao markers. It gives the module's purpose, scripts, the six D6 gates, where the tests live, the `API_URL` proxy, `api.ts` as exemplar, and the `Data/` deny rule. Each point matches the code. The file is not in T1's declared files, but this edit was requested by F3.
3. **F4, resolved.** `.prettierignore` now lists only `AGENTS.md` and `CLAUDE.md` (plus `dist`, `node_modules` and `package-lock.json`), and it is in T1's declared files.
4. **Unchanged from attempt 1, still fine:** spec conformance for FR-3, D3 and S-3.1 to S-3.4/C1; the red TDD evidence (`redTests.changed` is empty); the licences under the PE decisions of 2026-10-23; and `npm audit` with 0 vulnerabilities.

## Findings (JSON)

```json
{"version":1,"findings":[
{"id":"F1","status":"resolved","severity":"medium","lens":"security","title":"The Vite dev server was allowed to serve the whole repository, including the confidential Data/Información restringida.md","file":"src/web/vite.config.ts","line":7,"evidence":"Now `fs: { allow: [\".\", \"../../tests/web\"], deny: DENEGADOS }`. DENEGADOS re-declares Vite's default deny entries and adds `**/Data/**`. Curl results as reported by the Implementer (not reproduced by the Reviewer): the confidential file under /@fs/ and with ?raw gave 403, another Data/ file and the root CLAUDE.md gave 403, and /Data/ gave only the SPA index.html fallback."},
{"id":"F2","status":"open","severity":"medium","lens":"core","title":"The format and lint gates do not cover tests/web","file":"src/web/package.json","line":10,"evidence":"Unchanged. `prettier --check .` and `eslint .` run from src/web, so tests/web/api.test.ts is never formatted or linted. It has lines over the 110-column printWidth, and its 'sin detalles técnicos' describe callback is about 70 lines, over the 50-line limit. Advisory, because standards.md does not say whether its thresholds apply to tests. Recommend a decision before T2 and T3, which will add more tests. If tests are added to the gates, split the tests rather than delete cases."},
{"id":"F3","status":"resolved","severity":"medium","lens":"core","title":"src/web/AGENTS.md did not describe the new module","file":"src/web/AGENTS.md","line":15,"evidence":"A module section was added outside the Mandao markers: purpose, scripts, the six D6 gates, tests in tests/web, the API_URL proxy, api.ts as exemplar, and the Data/ deny rule. It matches the code."},
{"id":"F4","status":"resolved","severity":"low","lens":"core","title":".prettierignore was outside the declared files and its `*.md` was broader than needed","file":"src/web/.prettierignore","line":4,"evidence":"Narrowed to AGENTS.md and CLAUDE.md, and now in T1's declared files."},
{"id":"F5","status":"open","severity":"low","lens":"core","title":"The licence exception in the spec and in standards.md does not list MIT-0 and CC0-1.0","file":"especificaciones/MDO-0002-consultar-desde-la-interfaz/spec.md","line":245,"evidence":"Unchanged. The PE approved MIT-0 and CC0-1.0 on 2026-10-23. D7 and the Justified exceptions row still list only MPL-2.0, PSF-2.0, ISC, BlueOak-1.0.0 and CC-BY-4.0. standards.md#dependencies is to be updated at close."},
{"id":"F6","status":"open","severity":"low","lens":"security","title":"A valid 200 passes unknown fields through in `resultado`","file":"src/web/src/api.ts","line":79,"evidence":"Unchanged and advisory, as the Leader decided. Building `{ respuesta, fuentes, estado }` explicitly would keep fields outside the contract from reaching the UI."},
{"id":"F7","status":"open","severity":"low","lens":"core","title":"A caller's signal replaces the 30 s timeout, and AbortError is reported as a timeout","file":"src/web/src/api.ts","line":90,"evidence":"Unchanged and advisory, as the Leader decided. Relevant to T3 if it passes its own cancellation signal; `AbortSignal.any` would keep the 30 s limit. No test covers the default 30 s timeout."}
]}
```
