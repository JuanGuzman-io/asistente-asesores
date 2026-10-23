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

## T2 — attempt 1

VERDICT: FAIL

The fail comes from two blocking findings: D4's `white-space: pre-wrap` is missing (F1), and the module's AGENTS.md was not updated (F2). The out-of-scope changes have a sound technical reason (F3, F4). The aliases cannot load a second React copy in Vitest, and they do not widen what the dev server serves. Whether the dev server still runs with the aliases is unverified (F5).

## Spec conformance (T2, AC-1, AC-1/C2, AC-1/C3, S-2.1 to S-2.4/C3, D3, D4)
- **S-2.1:** met. The component shows the answer, the status, `documento > seccion` and the fragment (`src/web/src/Resultado.tsx:38-39, 51-54`).
- **S-2.2 and S-2.3 (AC-1/C2):** met. Each status shows its own label, and "Sin fuentes" appears when there are no sources.
- **S-2.4 (AC-1/C3):** met. All service text is rendered as React text nodes. There is no `dangerouslySetInnerHTML` and no `<a>` element. The tests also cover HTML in `documento` and `seccion`.
- **D4 (blocking, F1):** not met. D4 says "se pintan como nodos de texto de React con `white-space: pre-wrap`". No `white-space` exists anywhere in the web project; a search of the repo finds it only in `spec.md:177`. No later task picks it up, and T2 is the task that owns D4. Without it, line breaks in answers and fragments collapse into one line.
- **NFR-1:** met. The tests find elements by text and role.

## Test policy and TDD
- `loop.tdd.required` is true and red evidence exists (`red: true`). The Leader says the recorded failure is the missing `Resultado` module. `redTests.changed` is empty, so no red test was weakened.
- The tests are meaningful, with one weak case: S-2.2/C2 (`tests/web/Resultado.test.tsx:476-484`) compares the `textContent` of two different strings, so it cannot fail. S-2.3/C2 (line 496) is the test that actually checks each label is exclusive. Advisory (F6).
- No test cases were removed.
- Gate output as run: format, lint, typecheck, test (2 files, 28 tests) and build passed; audit was skipped. The red-style run of 9 tests is reported only by the Leader; its output is not in the pack.

## Out-of-scope changes: are they justified?
- **Why they are needed:** there is no `node_modules` or `package.json` at the repository root or under `tests/`. Bare imports from `tests/web/*.tsx` therefore cannot find `react` or `@testing-library/*` by walking up the directory tree.
- **`vite.config.ts` and `tsconfig.json`:** needed. However, the brief's `files` list is only `[Resultado.tsx, Resultado.test.tsx]`. The change should be recorded as an amendment to T2's files, as was done for T1 in commit ac657b0 (F3).
- **A simpler alternative was not considered:** `resolve.dedupe: ["react", "react-dom", "@testing-library/react", "@testing-library/dom"]` makes Vite resolve those packages from the project root. It needs no hand-built absolute paths. Alternatively, scope the alias to Vitest (`test.alias`) so the dev server and build are untouched (F5).
- **`.mandao/config.yml` (`tests.impacted`) and `mandao.lock`:** justified as tooling, since the gate-style and red-style runs start from different working directories. They are still outside T2's files and must be recorded the same way (F4). The command is also fragile (F7):
  - `{files}` is expanded without quotes, so paths with spaces break.
  - `"$B/$f"` breaks when `$f` is already absolute.

## Could the aliases load a second React copy?
- **In Vitest: no.** Only one copy exists on disk (`src/web/node_modules/react`). The alias points to that same directory, and `react-dom`'s own `require('react')` reaches the same file. The aliases, if anything, enforce a single copy.
- **The regexes are anchored:** `^react(/.*)?$` does not match `react-dom`. `$1` keeps subpaths such as `react/jsx-runtime` and `react-dom/client`.
- **Build: no problem.** The build passed, 14 modules in one bundle.
- **Dev server: OPEN, not verified.** The alias rewrites `react` to an absolute path inside `node_modules` before Vite decides whether to use its pre-bundled copy. That can leave some imports on the pre-bundled copy and others on the raw CommonJS file. The likely result is a CommonJS or default-export error, or "Invalid hook call". No gate runs `npm run dev`, so this cannot be confirmed from the pack (F5).
- **Minor:** `new URL(...).pathname` percent-encodes spaces and non-ASCII characters in the path; `fileURLToPath` is the safe form. Advisory (F8).

## Do the aliases widen what the dev server exposes?
No.
- `server.fs.allow` (`.` and `../../tests/web`) and `deny` are unchanged.
- The alias targets sit under `src/web/node_modules`, which `.` already allows.
- `Data/` and `.env*` stay denied.

## AGENTS.md (blocking, F2)
`src/web/AGENTS.md` mentions neither `Resultado.tsx` nor the new rule that `tests/web` resolves packages through `resolve.alias` and `tsconfig` `paths`. The next person to add a test dependency, for example `@testing-library/user-event` in T3, has to know to extend both lists.

## Accessibility lens
- **Structure: fine.** The labelled `section` with `aria-live="polite"` and the `h2` headings are adequate.
- **Advisory:**
  - The status label is set apart only by its text, not by a role. A `role="status"` would help screen readers, and visual styling per status would help sighted users.
  - The live region announces the whole result at once.

## Findings (JSON)
```json
{"version":1,"findings":[
{"id":"F1","status":"open","severity":"medium","lens":"core","title":"D4 requires white-space: pre-wrap for the answer and fragments; it is missing","file":"src/web/src/Resultado.tsx","line":54,"evidence":"spec.md:177 (D4): 'se pintan como nodos de texto de React con `white-space: pre-wrap`'. No white-space anywhere in src/web; T2 owns D4 and no later task covers it. Line breaks in answers and fragments collapse."},
{"id":"F2","status":"open","severity":"medium","lens":"core","title":"src/web/AGENTS.md does not reflect Resultado.tsx or the alias/paths rule for tests/web","file":"src/web/AGENTS.md","line":20,"evidence":"AGENTS.md says tests live in tests/web but not that their package imports resolve only through resolve.alias (vite.config.ts:17) and tsconfig paths; a new test dependency must be added to both lists."},
{"id":"F3","status":"open","severity":"medium","lens":"core","title":"vite.config.ts and tsconfig.json changed outside T2's declared files without a recorded amendment","file":"src/web/vite.config.ts","line":17,"evidence":"Brief files are [src/web/src/Resultado.tsx, tests/web/Resultado.test.tsx]. The change is technically needed (no node_modules at the repo root or under tests/), but it must be recorded as a T2 file amendment, as done for T1 in ac657b0."},
{"id":"F4","status":"open","severity":"low","lens":"core","title":".mandao/config.yml tests.impacted and mandao.lock changed outside T2's files","file":".mandao/config.yml","line":32,"evidence":"Justified as tooling (run red and run gates start from different working directories), but not in the task's files and not recorded as an amendment."},
{"id":"F5","status":"open","severity":"medium","lens":"core","title":"The global resolve.alias also applies to the dev server; possible split between the pre-bundled and raw React is unverified; resolve.dedupe or test.alias is simpler","file":"src/web/vite.config.ts","line":17,"evidence":"The alias rewrites 'react' to an absolute node_modules path before Vite's pre-bundling lookup. No gate runs npm run dev. resolve.dedupe([...]) or test.alias would fix tests/web resolution without touching dev or build. OPEN: confirm npm run dev renders with no Invalid hook call or CommonJS error, or narrow the alias."},
{"id":"F6","status":"open","severity":"low","lens":"core","title":"S-2.2/C2 test cannot fail","file":"tests/web/Resultado.test.tsx","line":476,"evidence":"It compares the textContent of 'Exitosa' with that of 'Sin información suficiente', which always differ. S-2.3/C2 (line 496) is the real check. Advisory."},
{"id":"F7","status":"open","severity":"low","lens":"core","title":"tests.impacted command breaks on paths with spaces or absolute paths","file":".mandao/config.yml","line":32,"evidence":"'set -- {files}' is unquoted and printf '%s/%s' \"$B\" \"$f\" prefixes even absolute paths. Advisory."},
{"id":"F8","status":"open","severity":"low","lens":"core","title":"URL.pathname used as a file path","file":"src/web/vite.config.ts","line":8,"evidence":"pathname percent-encodes spaces and non-ASCII; fileURLToPath from node:url is the correct conversion. Advisory."},
{"id":"F9","status":"open","severity":"low","lens":"accessibility","title":"Status label is set apart only by its text","file":"src/web/src/Resultado.tsx","line":49,"evidence":"<strong>{resultado.estado}</strong> has no role and no per-status styling. role=\"status\" or a data attribute per status would make it easier to tell apart. Advisory; the AC is met by the distinct text."}
]}
```

## T2 — attempt 2

VERDICT: PASS

This is the review of T2 attempt 2, from `/Users/jguzman/GitHub/Projects/asistente-asesores.worktrees/MDO-0002-consultar-desde-la-interfaz/.mandao/cache/MDO-0002/reviews/T2-2-pack.md`. I checked it against the attempt 1 findings. No blocking findings are left; only F6 and F9 stay open, both advisory.

## What changed and how I judged it
- **F1 (D4): resolved.** `PRE_WRAP = { whiteSpace: "pre-wrap" }` is set on the answer `<p>` (`src/web/src/Resultado.tsx:381`) and on each fragment `<blockquote>` (line 366). Text is still rendered only as React text nodes, with no `dangerouslySetInnerHTML`.
- **F5: resolved.**
  - The aliases moved from `resolve.alias` to `test.alias` (`src/web/vite.config.ts:429`), which applies only to Vitest.
  - `resolve`, `server.fs.allow`/`deny`, `proxy` and `preview` are the same as in T1, so the dev server and build behave as in T1. Nothing new is exposed, and the dev server cannot split React between two copies.
  - In Vitest there is still a single physical copy, `src/web/node_modules/react`; the repo root and `tests/` have no `node_modules`.
  - The `npm run dev` / `curl` check is reported by the Implementer; its output is not in the pack, so I have not verified it independently. With the aliases scoped to tests, it is no longer needed to settle the risk.
- **F8: resolved.** The alias paths now go through `decodeURIComponent(new URL(...).pathname)`, which is correct on macOS and Linux. `fileURLToPath` would also handle Windows drive paths; this is optional.
- **F2: resolved.** `src/web/AGENTS.md` now documents `Resultado.tsx` with D4 (text only, pre-wrap). It also states the rule that a new test dependency goes into both `test.alias` and the tsconfig `paths`.
- **F3 and F4: resolved.** The brief's `files` list and `tasks.md:78` now list `vite.config.ts`, `tsconfig.json`, `AGENTS.md`, `.mandao/config.yml` and `mandao.lock`. The Leader says this spec edit goes into its own docs commit before the task commit; I could not confirm that from the pack.
- **F7: resolved.**
  - The loop keeps absolute paths as they are, puts the repo-root prefix (`$B`) on relative ones, and passes the list as `"$@"` without reordering it.
  - Because Mandao JSON-quotes paths that contain spaces, those paths are safe.
  - The Leader's mixed-path check (28 tests) is reported, not shown in the pack.

## Spec, tests and TDD
- **Spec:** AC-1, AC-1/C2, AC-1/C3 and S-2.1 to S-2.4/C3 are met, as in attempt 1.
- **TDD:** red evidence is recorded (`red: true`). `redTests.changed` is empty, and the test file's hash is unchanged since attempt 1 (`d27e8367...`), so no red test was weakened.
- **Gates** (`/Users/jguzman/GitHub/Projects/asistente-asesores.worktrees/MDO-0002-consultar-desde-la-interfaz/.mandao/cache/MDO-0002/gates/T2-2.md`): format, lint, typecheck, test (2 files, 28 tests passed) and build passed; audit was skipped.
- **Module boundaries:** respected. `Resultado.tsx` imports only types from `./api`.

## Findings (JSON)
```json
{"version":1,"findings":[
{"id":"F1","status":"resolved","severity":"medium","lens":"core","title":"D4 white-space: pre-wrap on the answer and fragments","file":"src/web/src/Resultado.tsx","line":381,"evidence":"PRE_WRAP is applied to the answer <p> (381) and to the fragment <blockquote> (366)."},
{"id":"F2","status":"resolved","severity":"medium","lens":"core","title":"src/web/AGENTS.md reflects Resultado.tsx and the test.alias/paths rule","file":"src/web/AGENTS.md","line":342,"evidence":"New bullets cover Resultado (D4) and the rule to add test dependencies to both test.alias and tsconfig paths."},
{"id":"F3","status":"resolved","severity":"medium","lens":"core","title":"vite.config.ts and tsconfig.json added to T2's files","file":"especificaciones/MDO-0002-consultar-desde-la-interfaz/tasks.md","line":78,"evidence":"tasks.md:78 and brief.task.files now list them. The separate docs commit is stated by the Leader, not visible in the pack."},
{"id":"F4","status":"resolved","severity":"low","lens":"core","title":".mandao/config.yml and mandao.lock added to T2's files","file":"especificaciones/MDO-0002-consultar-desde-la-interfaz/tasks.md","line":78,"evidence":"Listed in tasks.md:78 and in the brief."},
{"id":"F5","status":"resolved","severity":"medium","lens":"core","title":"Aliases scoped to Vitest; dev server and build unchanged","file":"src/web/vite.config.ts","line":429,"evidence":"Moved to test.alias; resolve and server settings are as in T1. The dev-server curl check is reported by the Implementer; its output is not in the pack."},
{"id":"F6","status":"open","severity":"low","lens":"core","title":"S-2.2/C2 test cannot fail","file":"tests/web/Resultado.test.tsx","line":504,"evidence":"It compares the textContent of two different literal labels. S-2.3/C2 (line 524) is the effective check. Advisory."},
{"id":"F7","status":"resolved","severity":"low","lens":"core","title":"tests.impacted handles absolute paths and quoting","file":".mandao/config.yml","line":315,"evidence":"The case statement keeps absolute paths and prefixes relative ones with $B; the list is passed as \"$@\". The Leader's mixed-path run (28 tests) is reported, not shown."},
{"id":"F8","status":"resolved","severity":"low","lens":"core","title":"Alias paths decoded","file":"src/web/vite.config.ts","line":419,"evidence":"decodeURIComponent(new URL(...).pathname) is correct on POSIX. fileURLToPath would also cover Windows; optional."},
{"id":"F9","status":"open","severity":"low","lens":"accessibility","title":"Status label is set apart only by its text","file":"src/web/src/Resultado.tsx","line":378,"evidence":"<strong>{resultado.estado}</strong> has no role and no per-status styling. Advisory; the AC is met by the distinct text."}
]}
```
