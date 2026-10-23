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

## T3 — attempt 1

VERDICT: PASS

Review of MDO-0002 T3, attempt 1. I checked the pack at /Users/jguzman/GitHub/Projects/asistente-asesores.worktrees/MDO-0002-consultar-desde-la-interfaz/.mandao/cache/MDO-0002/reviews/T3-1-pack.md against spec.md (FR-1, FR-3, FR-4, NFR-1, D3), tasks.md T3 "Done when", src/web/AGENTS.md, and the files the diff depends on: api.ts, Resultado.tsx, tsconfig.json and tests/web/api.test.ts.

## Conformance

- **S-1.1 / AC-1:** passes. The "Procesando consulta…" region shows while the request is pending. On a 200 the state becomes `completado` and `Resultado` renders.
- **S-1.2 / C1 (double submit):** the guard holds at both points.
  - Button: `disabled={procesando}`.
  - Handler: `if (estado === "procesando") return;` runs after `preventDefault()`.
  - The tests cover a second click and Enter in the field, and both expect a single `fetch` call. See F1 for a limit on what those tests prove.
- **D3:** `EstadoProcesamiento` is the union `"inactivo" | "procesando" | "completado" | "error"`, held in `useState<EstadoProcesamiento>("inactivo")`. There is no state or request library, which matches the rejected alternatives in D3.
- **T1 advisory (`signal`):** confirmed. App calls `consultar(pregunta)` with no options, so `AbortSignal.timeout(30_000)` still applies (api.ts line 90). src/web/AGENTS.md records this.
- **AC-2 / FR-3:** passes. App shows only the `mensaje` and `codigoReferencia` from the client. api.ts never throws and never returns the raw body, so the `await` without try/catch does not swallow an error. The reference code renders as "Código de referencia: X", which matches S-3.1.
- **AC-2/C2 / FR-4 / S-4.1:** passes. The question is never cleared. After an error the input is editable and the button enabled. A new submit clears the previous result or error before `procesando`, and both paths are tested.
- **main.tsx:** mounts `<App />` inside `StrictMode`.
- **vite.config.ts:** adds `@testing-library/user-event` to `test.alias`. tsconfig.json already resolves it through the existing `"@testing-library/*"` wildcard in `paths`, so the "add it in both" rule in AGENTS.md is met without editing tsconfig. tsconfig.json is in the declared `files` but is unchanged, which is fine.
- **AGENTS.md:** src/web/AGENTS.md describes App, the two-level guard, keeping the question, and not passing `signal`.
- **Clean code / module boundaries:** no blocking issues. App uses only the public exports of `./api` and `./Resultado`. There are no magic numbers in business rules, and the style matches the exemplar `Resultado.tsx`.
- **TDD:** `loop.tdd.red` is true with evidence `red`, and `redTests.changed` is empty, so no red test was weakened. ASSUMPTION: I accept the red evidence as recorded in the brief. I did not see the red run's output.
- **Gates:** format, lint, typecheck, test (3 files, 38 tests passed) and build all pass according to .mandao/cache/MDO-0002/gates/T3-1.md. Audit was SKIPPED. That output does not break results down per file, so I make no per-test claim beyond "test gate passed".

## Accessibility lens

- **Label:** the `<label>` wraps the input with the text "Pregunta", and the test finds it with `getByLabelText("Pregunta")`.
- **Live region:** `role="status" aria-live="polite"` is always mounted and its text changes, which is the correct pattern.
- **Alert:** errors use `role="alert"`.
- **Queries:** every query in the tests is by role, label or text, never by class or id, as NFR-1 requires.
- **Advisories:** see F2 and F3.

## Findings (JSON)

```json
{"version":1,"findings":[
{"id":"F1","status":"open","severity":"low","lens":"core","title":"Handler-level double-submit guard is not exercised independently by tests","file":"tests/web/App.test.tsx","line":477,"evidence":"Both S-1.2/C1 tests run with the button already disabled. A disabled default button stops clicks, and it also stops implicit submission on Enter (HTML spec, which user-event follows). So the `if (estado === \"procesando\") return;` guard in App.tsx:332 is never what stops the second request. The guard exists and is correct under React's synchronous flush of discrete events. Advisory: add a test that submits the form directly (e.g. fireEvent.submit on the form) while processing, or make the guard more robust with a useRef flag. Not blocking: the task's Done-when (neither button nor keyboard sends another request) is met and tested."},
{"id":"F2","status":"open","severity":"low","lens":"accessibility","title":"Result live region is mounted already filled, so screen readers may not announce it","file":"src/web/src/App.tsx","line":363,"evidence":"`{resultado && <Resultado .../>}` inserts the `<section aria-live=\"polite\">` from Resultado.tsx together with its content. Many screen readers only announce changes inside a live region that already exists. NFR-1 says the result is announced in a polite region. Advisory: keep a persistent live container in App, or put a short completion message (e.g. \"Consulta completada\") in the existing role=status region. The error is not affected, because role=alert is announced on insertion."},
{"id":"F3","status":"open","severity":"low","lens":"core","title":"App-level 'S-3.1' test uses a 500 fixture, not the scenario's 422 with detail","file":"tests/web/App.test.tsx","line":86,"evidence":"S-3.1's Given is 422 problem+json with detail \"La pregunta no puede estar vacía.\" and requestId abc-123. The App test uses `{requestId:\"abc-123\", detail:\"interno\"}` with status 500, which is S-3.2, and asserts the generic message. The 422 mapping is covered in tests/web/api.test.ts:47, and the T3 Done-when asks only for an error with role=alert and its reference code, which the test does check. Advisory: use the 422 fixture so the test matches its label."}
]}
```

## T4 — attempt 1

VERDICT: FAIL

Review of MDO-0002 T4, attempt 1. I read the pack (`.mandao/cache/MDO-0002/reviews/T4-1-pack.md`) and checked it against these files: spec.md (D5, S-1.1, S-2.1, S-2.2, S-3.1, P1), tasks.md T4, `src/web/src/App.tsx`, `src/web/src/Resultado.tsx`, `src/web/src/api.ts`, `src/web/vite.config.ts`, `src/web/tsconfig.json`, `src/web/package.json`, `constitucion/business-rules.md` (BR-3) and `constitucion/model-registry.md`.

As agreed, I am not failing T4 because the E2E run is missing. The run is DEFERRED by PE decision (R-1). The only evidence is `npx playwright test --list`, which found 3 tests. Nothing here claims any e2e passed. The verdict is FAIL for one reason: the S-3.1 test would pass on errors other than S-3.1 (F1). F2 and F3 are cheap changes that make the deferred run much more likely to pass on the first try. I would fix all three in the same attempt.

## Would the tests prove the scenarios against the real backend?

- **S-1.1:** mostly yes. The test fills "Pregunta", clicks "Consultar", expects "Procesando consulta…" to be visible, then the result region, then the processing text to be hidden. That matches App.tsx (`role="status"`) and Resultado.tsx (`aria-label="Resultado de la consulta"`).
  - The `completado` state is only inferred from the result appearing. That is acceptable, because the state is not rendered as text.
  - Two risks: the 5 s default `expect` timeout (F2), and a small race on "Procesando…" if the extractive mode answers in a few milliseconds (F5, advisory).
- **S-2.1:** partly. It checks the exact "Exitosa" status, the "Respuesta" heading and the source label. None of these depends on generated wording, which is correct: the answer text is not asserted.
  - "Exitosa" and the source label do depend on retrieval and on the output guardrail of MDO-0001. That is inherent to running against the real backend and acceptable.
  - Gaps: the scenario says "con su fragmento", but no fragment is asserted (F4). And the source locator will hit a strict-mode error if two fragments come from the same section (F3).
- **S-2.2:** yes. It relies on BR-3 (a fixed message) and DP-6 (below the threshold the model is not called), so it does not depend on generated wording.
  - `getByText("Sin información suficiente")` is a case-insensitive substring match. The fixed answer "No tengo información suficiente para responder." does not contain "sin información suficiente", so there is no strict-mode collision.
  - The scenario's "rótulo distinto del de Exitosa" is not asserted (part of F4). It is already covered by the unit tests in T2.
- **S-3.1:** not proven (F1). The test only checks that `role="alert"` contains "Código de referencia:". In api.ts, `requestId` is passed through for every non-200 problem response. So a 500, 413 or 415 with a `requestId` would also pass, as would a backend that crashes on empty input.
  - The assertion should pin the 422 rejection. Option A: `page.waitForResponse` on `/api/consultar` and assert `status() === 422`. Option B: assert that the alert does not show the generic message and that the reference code is not empty, for example `toContainText(/Código de referencia: \S+/)`.
  - The backend's `detail` text is fixed contract text, not generated, so asserting it would also be valid. But I could not confirm the exact MDO-0001 wording from this worktree (ASSUMPTION; P1 only says `detail` exists), so the status check is the safer choice.
  - The `error` processing state is not rendered, so the alert is the right proxy for it.

## Type-checking decision

Excluding `tests/web/e2e` from `tsc --noEmit` is acceptable:
- The e2e suite is not a gate.
- Playwright transpiles the spec without checking types.
- The spec is 52 lines and only uses `@playwright/test`.
- The reason is documented in `src/web/AGENTS.md`.

A small alternative, which I have not verified because I have no shell (OPEN): add a script `"typecheck:e2e": "tsc --noEmit -p ../../tests/web/e2e/tsconfig.json"`. TypeScript maps a `paths` target ending in `.js` to the sibling `index.d.ts`, so the existing e2e tsconfig may already type-check without touching the root tsconfig, which is what broke Playwright's config loading. If that works, it can be run by hand next to `npm run e2e`. This is advisory, not a condition of PASS.

## Other checks

- **Scope:** all changed paths are in the amended `files`. `package.json` already has `@playwright/test` 1.64.1 and the `e2e` script, so it is not in this diff.
- **Vitest:** `vite.config.ts` excludes `tests/web/e2e/**` and only picks up `*.test.*`, so Vitest will not try to run the Playwright spec. The test gate passed.
- **AGENTS.md:** `src/web/AGENTS.md` describes how to run e2e, that the backend is a prerequisite, that e2e is not a gate, and the tsconfig split. Correct.
- **Module boundaries:** the tests only drive the UI, through roles, labels and text (NFR-1). No internals are touched.
- **Security lens (risk tag public-api):** no findings. The dev server binds to 127.0.0.1 and there are no secrets. `Data/` serving is unchanged (`fs.deny`).
- **TDD:** `loop.tdd.required` is false and the tasks.md notes justify it. No red evidence is needed.

## Findings (JSON)

```json
{"version":1,"findings":[
{"id":"F1","status":"open","severity":"medium","lens":"core","title":"S-3.1 e2e does not prove the 422 empty-question rejection","file":"tests/web/e2e/consultar.spec.ts","line":42,"evidence":"Only asserts the alert contains 'Código de referencia:'. api.ts passes requestId through for every non-200 problem response, so a 500/413/415 with requestId, or a backend crash on empty input, also passes. Assert the 422 via page.waitForResponse(r => r.url().endsWith('/api/consultar')) with status() === 422, and/or assert the alert is not the generic message and the code is non-empty (/Código de referencia: \\S+/)."},
{"id":"F2","status":"open","severity":"medium","lens":"core","title":"Default 5 s expect timeout and 30 s test timeout are too short for the real backend","file":"src/web/playwright.config.ts","line":4,"evidence":"The result assertions use Playwright's default 5 s expect timeout, but the backend calls Gemini plus local embeddings (model-registry.md) and the client allows 30 s (TIEMPO_LIMITE_MS). The default test timeout of 30 s equals the client timeout, so the test is killed before a client timeout error could show. Set e.g. expect: { timeout: 35_000 } and timeout: 60_000 in defineConfig. ASSUMPTION: real latency is above 5 s on a cold or first query."},
{"id":"F3","status":"open","severity":"medium","lens":"core","title":"Source locator fails in strict mode if two fragments share a section","file":"tests/web/e2e/consultar.spec.ts","line":28,"evidence":"getByText('Productos de Crédito > Crédito Productivo Impulso') must match exactly one element. Resultado.tsx renders one <strong> per fragment, so top-k retrieval returning two fragments from the same section causes a strict-mode violation. Use .first(). OPEN: whether MDO-0001 deduplicates sources by section."},
{"id":"F4","status":"open","severity":"low","lens":"core","title":"S-2.1 fragment and S-2.2 distinct label not asserted end to end","file":"tests/web/e2e/consultar.spec.ts","line":28,"evidence":"S-2.1 says 'con su fragmento', but there is no assertion that the source item has a non-empty blockquote. For S-2.2, a cheap check is resultado.getByText('Exitosa', { exact: true }) toHaveCount(0). Both are covered at unit level, so this is advisory."},
{"id":"F5","status":"open","severity":"low","lens":"core","title":"Possible race on 'Procesando consulta…' with a fast extractive backend","file":"tests/web/e2e/consultar.spec.ts","line":18,"evidence":"Without a Gemini key the extractive mode may answer before the first poll sees the status text. Advisory; acceptable for a real-backend test, but note it if the run is flaky."},
{"id":"F6","status":"open","severity":"low","lens":"core","title":"e2e spec excluded from tsc; a separate -p check may be possible","file":"src/web/tsconfig.json","line":22,"evidence":"The exclusion is acceptable and documented. An optional 'typecheck:e2e': 'tsc --noEmit -p ../../tests/web/e2e/tsconfig.json' script could type-check the spec without changing root paths. Not verified (no shell)."}
]}
```

## T4 — attempt 2

VERDICT: PASS

I reviewed T4 attempt 2 against `/Users/jguzman/GitHub/Projects/asistente-asesores.worktrees/MDO-0002-consultar-desde-la-interfaz/.mandao/cache/MDO-0002/reviews/T4-2-pack.md`. F1–F4 and F6 are fixed, and nothing in the diff is blocking. F5 is low and only advisory.

The e2e run is still DEFERRED by PE decision (R-1). I am not treating any e2e test as passed. The only evidence is `--list`, which found 3 tests. I also have no output for `npm run typecheck:e2e`: it is not in the pack's gate results, so it is only the Implementer's claim (ASSUMPTION). The same goes for the `--list` count after the e2e tsconfig `paths` changed to the package directory: the pack does not show it was re-run (ASSUMPTION). Re-running `npx playwright test --list` once confirms that Playwright still loads with the new mapping.

## Re-check by finding

- **F1, resolved.** The test starts `waitForResponse` before the click, so it cannot miss the response.
  - It asserts `status() === 422`, the alert matches `/Código de referencia: \S+/`, and the generic message is not shown.
  - So a 500, 413 or 415 with a `requestId` no longer passes, and the test now proves S-3.1 against the real backend.
  - Nothing depends on the backend's `detail` wording.
- **F2, resolved.** `timeout` is 60_000 and `expect.timeout` is 35_000. Both cover the client's 30 s limit, and AGENTS.md documents them.
- **F3, resolved.** The source is found with `getByRole("listitem").filter({ hasText }).first()`. This avoids the strict-mode error when two fragments share a section.
- **F4, resolved.**
  - S-2.1 now asserts that the source's `blockquote` is not empty.
  - S-2.2 asserts that an exact "Exitosa" appears 0 times. That assertion can't pass before the result renders, because the earlier "Sin información suficiente" and "Sin fuentes" checks wait for the result region first.
- **F5, open (low, advisory).** Unchanged: the check that "Procesando consulta…" is visible can race if the extractive mode (no Gemini key) answers within a few milliseconds. Note it if the deferred run turns out flaky.
- **F6, resolved.**
  - `typecheck:e2e` runs `tsc --noEmit -p ../../tests/web/e2e/tsconfig.json`. That tsconfig maps `@playwright/test` to the package directory, relative to the e2e tsconfig itself.
  - Its `paths` replaces the inherited ones instead of merging with them. That is fine, because the spec only imports `@playwright/test`.
  - It is not a gate, and AGENTS.md documents it.

## Other checks

- **Scope:** every changed path is in T4's amended `files`. `package.json` only adds the `typecheck:e2e` script.
- **Gates:** format, lint, typecheck, test, build and audit all passed with exit code 0.
- **Vitest:** it still excludes `tests/web/e2e/**`.
- **AGENTS.md:** `src/web/AGENTS.md` describes the e2e setup, its prerequisites, the timeouts and the type-check split.
- **Generated wording:** no assertion depends on it. The assertions only use roles, labels, the status values, the source label, the fixed BR-3 "Sin fuentes" path, and the HTTP status.
- **Security lens (risk tag public-api):** no findings.
- **TDD:** not required, as tasks.md justifies.
- **Module boundaries:** respected. The tests only drive the UI.

## Findings (JSON)

```json
{"version":1,"findings":[
{"id":"F1","status":"resolved","severity":"medium","lens":"core","title":"S-3.1 e2e does not prove the 422 empty-question rejection","file":"tests/web/e2e/consultar.spec.ts","line":363,"evidence":"Now starts waitForResponse before the click, asserts status() === 422, the alert matches /Código de referencia: \\S+/, and the generic message is absent."},
{"id":"F2","status":"resolved","severity":"medium","lens":"core","title":"Default 5 s expect timeout and 30 s test timeout are too short for the real backend","file":"src/web/playwright.config.ts","line":8,"evidence":"timeout: 60_000 and expect: { timeout: 35_000 } cover the client's 30 s limit; documented in AGENTS.md."},
{"id":"F3","status":"resolved","severity":"medium","lens":"core","title":"Source locator fails in strict mode if two fragments share a section","file":"tests/web/e2e/consultar.spec.ts","line":349,"evidence":"Uses getByRole('listitem').filter({ hasText }).first()."},
{"id":"F4","status":"resolved","severity":"low","lens":"core","title":"S-2.1 fragment and S-2.2 distinct label not asserted end to end","file":"tests/web/e2e/consultar.spec.ts","line":354,"evidence":"Asserts the blockquote is not empty (S-2.1) and that an exact 'Exitosa' appears 0 times in the result region, after the region has rendered (S-2.2)."},
{"id":"F5","status":"open","severity":"low","lens":"core","title":"Possible race on 'Procesando consulta…' with a fast extractive backend","file":"tests/web/e2e/consultar.spec.ts","line":340,"evidence":"Unchanged. Advisory: if the extractive mode answers within a few ms, the visibility check can miss the status text. Note it if the deferred run is flaky."},
{"id":"F6","status":"resolved","severity":"low","lens":"core","title":"e2e spec excluded from tsc; a separate -p check may be possible","file":"src/web/package.json","line":15,"evidence":"Added 'typecheck:e2e' using tests/web/e2e/tsconfig.json, with paths pointing to the @playwright/test package dir; not a gate; documented. The pack has no run output for it: the Implementer's claim that it passes is not verified here (ASSUMPTION)."}
]}
```

## T5 — attempt 1

VERDICT: PASS

I'm not stating my model name. The reviewer persona rules say "Do not say which model you are; Mandao records who reviewed from what it invoked." The brief already records `loop.reviewer.model`.

## Findings (JSON)

```json
{"version":1,"findings":[
{"id":"F1","status":"open","severity":"low","lens":"core","title":"e2e S-3.1 still expects an empty question to reach the backend; T5 breaks it until T6 lands","file":"tests/web/e2e/consultar.spec.ts","line":33,"evidence":"Line 34 says 'el clic con el campo vacío llega al backend' and line 38 expects a 422. The button is now disabled when the box is empty, so this e2e will time out. Not blocking: e2e is not a gate, and tasks.md T6 (line 182) replaces this test. src/web/AGENTS.md already describes the new behaviour. T6 must be done before the checkpoint 'npm --prefix src/web run e2e'."},
{"id":"F2","status":"open","severity":"low","lens":"core","title":"JS trim() and Python str.strip() treat a few whitespace characters differently","file":"src/web/src/pregunta.ts","line":5,"evidence":"D8 claims parity with ConsultaEntrada. Python strip() also removes \\x1c-\\x1f and \\x85. JS trim() also removes \\uFEFF, which Python does not. On these exotic edges the counter or the button can disagree with the backend by one. D8 keeps the backend as the authority and the 422 path is still handled (S-3.1), so this is advisory only. A comment in D8 or pregunta.ts would document it."},
{"id":"F3","status":"open","severity":"low","lens":"accessibility","title":"Counter contrast at 11px is not shown","file":"src/web/src/estilos.css","line":435,"evidence":".contador uses var(--tenue) at 0.6875rem. Nothing shows it meets 4.5:1 in light or dark mode. Over the limit, the state is also carried by aria-invalid, by font-weight and by the text itself ('1.001/1.000'), so it does not depend on colour alone. Advisory: check the contrast of --tenue."}
]}
```

## Spec conformance

- AC-1/C4: met. Compositor.tsx disables the button with `procesando || !preguntaValida(pregunta)`; App.tsx `enviar` also returns early when the question is not valid; the counter "N/1.000" uses a fixed thousands separator.
- S-1.3 and S-1.3/C4: covered by unit tests (empty, spaces and tabs disable the button and show "0/1.000"; click and Enter make no fetch; typing enables the button and shows "1/1.000"; newline covered in pregunta.test.ts).
- S-1.4 and S-1.4/C4: 1,001 code points show "1.001/1.000", aria-invalid="true", counter in the accessible description, button disabled, no fetch; exactly 1,000 accepted with emojis, decomposed é and surrounding spaces, fetch called once.
- D8: constant, largoPregunta and preguntaValida match the decision; no maxLength, required or .length; text sent as typed.
- Module boundaries: rule in its own pregunta.ts used by Compositor and App; not duplicated.
- Magic numbers: none (MAXIMO_PREGUNTA).
- Mock: the counter is not in the approved mock; justified by C-9 / D8, approved after the mock; follows the mock's look (--mono, --tenue).
- AGENTS.md: new entry for pregunta.ts, counter, aria-describedby/aria-invalid and the handler guard; e2e note updated.

## Lenses

- Security (input): client rule only improves UX; backend stays the authority; counter renders text only; no new dependencies.
- Accessibility: counter linked via aria-describedby; over-limit exposed with aria-invalid; button keeps the name "Consultar"; contrast advisory (F3).

## TDD (ADR 0022)

- RED run recorded for T5 before REPORTED (execution.md lines 40-41).
- redTests.changed, App.test.tsx "S-4.1: un nuevo envío limpia el resultado anterior": only change is typing "otra pregunta" before the second click; FR-4 (C-9) empties the box and C-9 forbids sending it empty; fetch-twice and cleared-result assertions intact; not a weakening.
- S-3.1 changed from enviar("") to enviar("x") with the 422 forced through the fetch mock; preserves intent.
- pregunta.test.ts: precomposed U+00E9 on line 17 and "e" + U+0301 on line 23; NFC case really exercised.

## Gates (as reported in the pack; I did not run them)

format, lint, typecheck, test and build: PASS. scan-markers: PASS. audit: SKIPPED. Not configured: secrets, sast, metrics.
