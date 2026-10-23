# Reviews

## T1 — attempt 1

VERDICT: PASS

I reviewed this as claude-opus-5-5.

T1 does what the spec asks and nothing blocks it. All four gates passed in the Leader's run (format, lint, `mypy --strict` on 8 source files, and pytest with 7 passed). I am relying on that output (`.mandao/cache/MDO-0001/gates/T1-1.md`) and did not rerun anything.

**Spec, clause by clause**
- **S-1.1 / AC-1:** the five official documents load, including `Políticas de Atención`, and every fragment has its document, section and text. The test checks the exact set of documents.
- **S-1.1/C1 / AC-1/C1:** nothing from the restricted file becomes a fragment. One test checks every meaningful line of that file against all fragments, without printing it. The "indexed term" and "vector" parts of C1 can't be tested yet because the search index isn't built in T1.
- **S-1.2:** a file marked `CONFIDENCIAL` in its first 10 lines is excluded even when it isn't on the list. The log names the file and contains none of its content or headings, and a test checks this.
- **Design decisions:** D1 is met (Python 3.13 pinned, `requires-python >=3.11,<3.15`). D2 is met: each `##` section with its `###` subsections is one fragment, and a file with no `##` is one fragment titled with its `#`. D3 is met: both exclusion layers are in place, and file names are normalized so the macOS name of `Información restringida.md` still matches.
- **The other done-when items in `tasks.md`:** the gates in `.mandao/config.yml` match the spec, the PE approved them in this session, and mypy runs in strict mode.

**Tests and TDD:** red evidence is in `execution.md`. The first run failed because `pytest` wasn't found (exit 127). The second failed with exit 2, which fits the module not existing yet. `redTests.changed` is empty, so no red test was weakened. The seven tests check real behaviour and none of them is noise.

**Layers and module boundaries:** `infraestructura/documentos` imports only `dominio.modelos.Fragmento`, which `design.md` places in `dominio`. Nothing reaches into another module's internals.

**Clean code:** no errors are swallowed, the 10-line limit and the `CONFIDENCIAL` marker are named constants, and names follow the glossary. There was no exemplar to follow. Files outside the brief's list (`__init__.py` files, `src/server/AGENTS.md` and `CLAUDE.md`, the ruff exclude for `especificaciones/`, `uv.lock`, `mandao.lock`) are justified.

**Security:** no open security finding. Confidential content is kept out of fragments and out of the log, as `security.md` requires. `.env.example` has no value, and `.env` is ignored by git.

## Findings (JSON)

```json
{"version":1,"findings":[
{"id":"F1","status":"open","severity":"low","lens":"security","title":"The CONFIDENCIAL header check matches case-sensitively and as a substring","file":"src/server/infraestructura/documentos/cargador.py","line":20,"evidence":"`MARCA_CONFIDENCIAL in linea` misses 'Confidencial' and matches 'CONFIDENCIALIDAD'. D3 says 'la palabra CONFIDENCIAL', so this is within spec. The name-list layer still protects the known file. Advisory: consider a case-insensitive whole-word match."},
{"id":"F2","status":"open","severity":"low","lens":"security","title":"No test shows the header layer alone excludes the real restricted file","file":"tests/server/infraestructura/documentos/test_cargador.py","line":580,"evidence":"The tests on real Data/ always pass [RESTRINGIDO] as excluded. The header layer is only tested with tmp_path fixtures. Advisory: add cargar_documentos(DATA, []) to show both layers work on the real data."},
{"id":"F3","status":"open","severity":"low","lens":"core","title":"Text before the first ## is dropped when a file has sections","file":"src/server/infraestructura/documentos/cargador.py","line":506,"evidence":"Lines between '#' and the first '##' are not stored anywhere. D2 doesn't cover this case, and a check found no official file in Data/ with such text. Advisory."},
{"id":"F4","status":"open","severity":"low","lens":"core","title":"'##' inside a fenced code block would start a new section","file":"src/server/infraestructura/documentos/cargador.py","line":504,"evidence":"The splitter doesn't track code fences. The current Data/ files are not affected. Advisory."},
{"id":"F5","status":"open","severity":"low","lens":"core","title":"Startup exclusion log is plain text, not JSON","file":"src/server/infraestructura/documentos/cargador.py","line":523,"evidence":"standards.md says logs are structured JSON. No logging setup exists yet, and the content-free rule is met. Advisory until the logging task lands."},
{"id":"F6","status":"open","severity":"low","lens":"core","title":"Root AGENTS.md module index still says no modules exist","file":"AGENTS.md","line":1,"evidence":"src/server/ now exists and has its own AGENTS.md. The root index still says 'aún no existen'. Advisory: update it when the next module is added."}
]}
```

ASSUMPTION: the second red run's exit 2 came from importing a module that didn't exist yet. The log records only the exit code, not the error text.
