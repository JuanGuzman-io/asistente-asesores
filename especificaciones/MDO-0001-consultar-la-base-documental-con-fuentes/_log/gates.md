# Gates

## T1 — attempt 1

Every configured gate passed; not configured: metrics; declared none: build.

| Gate | Status | Exit |
|---|---|---|
| format | PASS | 0 |
| lint | PASS | 0 |
| typecheck | PASS | 0 |
| test | PASS | 0 |
| build | SKIPPED | — |
| secrets | PASS | 0 |
| audit | SKIPPED | — |
| sast | PASS | 0 |

## T2 — attempt 1

Every configured gate passed; not configured: metrics; declared none: build.

| Gate | Status | Exit |
|---|---|---|
| format | PASS | 0 |
| lint | PASS | 0 |
| typecheck | PASS | 0 |
| test | PASS | 0 |
| build | SKIPPED | — |
| secrets | PASS | 0 |
| audit | SKIPPED | — |
| sast | PASS | 0 |

## T3 — attempt 1

Every configured gate passed; not configured: secrets, audit, sast, metrics; declared none: build.

| Gate | Status | Exit |
|---|---|---|
| scan-markers | PASS | — |
| format | PASS | 0 |
| lint | PASS | 0 |
| typecheck | PASS | 0 |
| test | PASS | 0 |
| build | SKIPPED | — |

## T3 — attempt 2

Every configured gate passed; not configured: metrics; declared none: build.

| Gate | Status | Exit |
|---|---|---|
| format | PASS | 0 |
| lint | PASS | 0 |
| typecheck | PASS | 0 |
| test | PASS | 0 |
| build | SKIPPED | — |
| secrets | PASS | 0 |
| audit | SKIPPED | — |
| sast | PASS | 0 |

## T4 — attempt 1

Every configured gate passed; not configured: metrics; declared none: build.

| Gate | Status | Exit |
|---|---|---|
| scan-markers | PASS | — |
| format | PASS | 0 |
| lint | PASS | 0 |
| typecheck | PASS | 0 |
| test | PASS | 0 |
| build | SKIPPED | — |
| secrets | PASS | 0 |
| audit | SKIPPED | — |
| sast | PASS | 0 |

## T4 — attempt 2

Every configured gate passed; not configured: metrics; declared none: build.

| Gate | Status | Exit |
|---|---|---|
| scan-markers | PASS | — |
| format | PASS | 0 |
| lint | PASS | 0 |
| typecheck | PASS | 0 |
| test | PASS | 0 |
| build | SKIPPED | — |
| secrets | PASS | 0 |
| audit | SKIPPED | — |
| sast | PASS | 0 |

## T5 — attempt 1

Every configured gate passed; not configured: metrics; declared none: build.

| Gate | Status | Exit |
|---|---|---|
| scan-markers | PASS | — |
| format | PASS | 0 |
| lint | PASS | 0 |
| typecheck | PASS | 0 |
| test | PASS | 0 |
| build | SKIPPED | — |
| secrets | PASS | 0 |
| audit | SKIPPED | — |
| sast | PASS | 0 |

## T6 — attempt 1

Every configured gate passed; not configured: metrics; declared none: build.

| Gate | Status | Exit |
|---|---|---|
| scan-markers | PASS | — |
| format | PASS | 0 |
| lint | PASS | 0 |
| typecheck | PASS | 0 |
| test | PASS | 0 |
| build | SKIPPED | — |
| secrets | PASS | 0 |
| audit | SKIPPED | — |
| sast | PASS | 0 |

## T8 — attempt 1

Every configured gate passed; not configured: metrics; declared none: build.

| Gate | Status | Exit |
|---|---|---|
| scan-markers | PASS | — |
| format | PASS | 0 |
| lint | PASS | 0 |
| typecheck | PASS | 0 |
| test | PASS | 0 |
| build | SKIPPED | — |
| secrets | PASS | 0 |
| audit | SKIPPED | — |
| sast | PASS | 0 |

## T8 — attempt 2

Every configured gate passed; not configured: metrics; declared none: build.

| Gate | Status | Exit |
|---|---|---|
| scan-markers | PASS | — |
| format | PASS | 0 |
| lint | PASS | 0 |
| typecheck | PASS | 0 |
| test | PASS | 0 |
| build | SKIPPED | — |
| secrets | PASS | 0 |
| audit | SKIPPED | — |
| sast | PASS | 0 |

## T7 — attempt 1

Every configured gate passed; not configured: metrics; declared none: build.

| Gate | Status | Exit |
|---|---|---|
| scan-markers | PASS | — |
| format | PASS | 0 |
| lint | PASS | 0 |
| typecheck | PASS | 0 |
| test | PASS | 0 |
| build | SKIPPED | — |
| secrets | PASS | 0 |
| audit | PASS | 0 |
| sast | PASS | 0 |

## T9 — attempt 1

Every configured gate passed; not configured: metrics; declared none: build.

| Gate | Status | Exit |
|---|---|---|
| scan-markers | PASS | — |
| format | PASS | 0 |
| lint | PASS | 0 |
| typecheck | PASS | 0 |
| test | PASS | 0 |
| build | SKIPPED | — |
| secrets | PASS | 0 |
| audit | SKIPPED | — |
| sast | PASS | 0 |

## T10 — attempt 1

A gate failed; not configured: metrics; declared none: build.

| Gate | Status | Exit |
|---|---|---|
| scan-markers | PASS | — |
| format | PASS | 0 |
| lint | PASS | 0 |
| typecheck | PASS | 0 |
| test | FAIL | 4 |
| build | SKIPPED | — |
| secrets | FAIL | 1 |
| audit | PASS | 0 |
| sast | PASS | 0 |

### test — FAIL (1 of 1 lines naming the task's files)

```
ERROR: not found: /Users/jguzman/GitHub/Projects/asistente-asesores.worktrees/MDO-0001-consultar-la-base-documental-con-fuentes/tests/fixtures/consultas.json
```

### secrets — FAIL (no line names the task's files: the last 9 of 9 lines)

```
ERROR: Potential secrets about to be committed to git repo!
Secret Type: Secret Keyword
Location:    tests/server/http/test_consultar_api.py:323
Possible mitigations:
  - For information about putting your secrets in a safer place, please ask in
    #security
  - Mark false positives with an inline `pragma: allowlist secret` comment
If a secret has already been committed, visit
https://help.github.com/articles/removing-sensitive-data-from-a-repository
```

## T10 — attempt 2

A gate failed; declared none: build.

| Gate | Status | Exit |
|---|---|---|
| scan-markers | PASS | — |
| format | PASS | 0 |
| lint | PASS | 0 |
| typecheck | PASS | 0 |
| test | FAIL | 4 |
| build | SKIPPED | — |
| secrets | PASS | 0 |
| audit | PASS | 0 |
| sast | PASS | 0 |
| metrics | PASS | 0 |

### test — FAIL: the same 1 lines as attempt 1
