# Backend (`src/server/`)

Python 3.13 con `uv`. Gates: `uv run ruff format --check .`, `uv run ruff check .`, `uv run mypy src` (strict), `uv run pytest`.

- `dominio/modelos.py`: `Fragmento(documento, seccion, texto)`.
- `config.py`: directorio `Data/` y lista de excluidos (`Información restringida.md`).
- `infraestructura/documentos/cargador.py`: `cargar_documentos(directorio, excluidos)` fragmenta por `##` (o `#` si no hay `##`). Excluye por lista y por `CONFIDENCIAL` en las primeras 10 líneas; el log nombra el archivo, nunca su contenido. Los nombres se normalizan a NFC.
