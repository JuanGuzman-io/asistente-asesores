# Premises

## P1 — run

- Claim: No existe código en `src/` ni en `tests/`
- Command: `git ls-files -- src tests` (from the worktree root)
- Ran at: 2026-10-23T14:53:24.259Z on 7929b7e
- Exit: 0

```

```

## P2 — run

- Claim: El `sqlite3` de Python 3.13 trae FTS5 y `remove_diacritics 2` pliega tildes
- Command: `python3 especificaciones/MDO-0001-consultar-la-base-documental-con-fuentes/_log/premises/probes/p2_sqlite.py` (from the worktree root)
- Ran at: 2026-10-23T15:00:12.450Z on 7929b7e
- Exit: 0

```
python 3.13.4 sqlite 3.54.0
fts5 credito -> 1
fts5 CRÉDITO -> 1
```

## P4 — run

- Claim: Todos los documentos oficiales de `Data/` se organizan en secciones `##` de menos de 1 KB
- Command: `python3 especificaciones/MDO-0001-consultar-la-base-documental-con-fuentes/_log/premises/probes/p4_sections.py` (from the worktree root)
- Ran at: 2026-10-23T14:53:25.736Z on 7929b7e
- Exit: 0

```
Manual del Asesor Comercial.md sections 3 max_bytes 164
Políticas de Atención.md sections 4 max_bytes 123
Portafolio de Microseguros.md sections 4 max_bytes 153
Procedimientos Operativos.md sections 3 max_bytes 179
Productos de Crédito.md sections 3 max_bytes 387
```

## P6 — run

- Claim: Qdrant en modo local bloquea su carpeta: un segundo cliente sobre el mismo `path` falla
- Command: `uv run --no-project --python 3.13 --with qdrant-client==1.20.0 python -I especificaciones/MDO-0001-consultar-la-base-documental-con-fuentes/_log/premises/probes/p6_qdrant_lock.py` (from the worktree root)
- Ran at: 2026-10-23T15:10:57.823Z on 9da22a0
- Exit: 0

```
Downloading grpcio (11.7MiB)
Downloading numpy (5.2MiB)
Downloading pydantic-core (1.9MiB)
 Downloaded pydantic-core
 Downloaded numpy
 Downloaded grpcio
Installed 20 packages in 18ms
python 3.13.16 qdrant-client 1.20.0
second client on same path: refused -> RuntimeError Storage folder /Users/jguzman/GitHub/Projects/asistente-asesores.worktrees/MDO-0001-consultar-la-base-documental-con-fuentes/.mandao/cache/MDO-0001/premises/tmp
```
