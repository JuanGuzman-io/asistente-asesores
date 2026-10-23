# Premises

## P1 — run

- Claim: `consultar` es el único código de `src/` que llama a `buscar`
- Command: `git grep -n '\.buscar(' -- src` (from the worktree root)
- Ran at: 2026-10-23T22:07:46.168Z on fd79dc8
- Exit: 0

```
src/server/AGENTS.md:10:- `dominio/puertos.py`: `ResultadoBusqueda(fragmentos, hay_soporte)` (hasta 3 fragmentos, mejor primero; vacío si no hay soporte), el Protocol `BuscadorDocumental.buscar(pregunta)`, `RespuestaRedactada(respuesta, fragmentos_usados, partes_sin_soporte=(), modo=None)` (`modo`: el de esa llamada; la ruta lo registra y solo lee `Redactor.modo` si viene vacío) (ids 1-based en la lista numerada entregada al redactor; `partes_sin_soporte` son las partes de la pregunta sin respaldo; las llena `RedactorGemini`), el Protocol `Redactor` (atributo `modo`: `modelo` o `extractivo`; método `redactar(pregunta, fragmentos)`) y el Protocol `RepositorioConsultas.registrar(*, request_id, pregunta, resultado, modo)`.
src/server/aplicacion/consultar.py:33:    busqueda = buscador.buscar(pregunta)
```

## P2 — run

- Claim: `consultas` ya acepta estado `BLOQUEADA` y modo `ninguno` sin migración
- Command: `uv run pytest -q tests/server/infraestructura/persistencia/test_repositorio.py -k 'bloqueada or modo'` (from the worktree root)
- Ran at: 2026-10-23T22:07:47.876Z on fd79dc8
- Exit: 0

```
.........                                                                [100%]
9 passed, 15 deselected in 0.04s
```
