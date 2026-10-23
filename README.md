# Asistente para asesores comerciales

Prueba técnica: asistente interno que responde consultas de asesores comerciales usando solo la base documental de `Data/`.

## Pruebas

Todo se prueba siempre, en dos comandos:

- `uv run pytest`: la lógica, sin red y sin descargar modelos (usa dobles de embeddings y de Gemini). Excluye las evaluaciones con `-m 'not eval'` (en `pyproject.toml`).
- `uv run pytest -m eval`: las evaluaciones EV-1 a EV-5 de calidad con el modelo real de embeddings, contra `tests/fixtures/consultas.json`. La primera vez descarga el modelo (0,22 GB); después corre sin red.

Los dos son gates de Mandao (`test` y `metrics` en `.mandao/config.yml`): ninguna tarea ni la spec pasan si falla cualquiera de ellos.

## Datos de prueba con aspecto de secreto

`Data/Información restringida.md` contiene un token interno y una clave temporal **falsos**: son datos irreales de la prueba, puestos ahí a propósito para comprobar que el asistente nunca indexa ni expone documentos confidenciales. No son credenciales reales.

El gate de secretos (`detect-secrets`, con la línea base en `.secrets.baseline`) no los marca hoy porque no coinciden con sus detectores. Si algún día los marca, se registran en la línea base como datos de prueba, no se borran del archivo. La línea base excluye los logs de Mandao (`_log/`), que solo guardan hashes sha256.

## Vulnerabilidades aceptadas

`.pip-audit-ignore` lista los avisos de pillow 12.3.0 que el PE aceptó el 2026-10-23 (MDO-0001 T3), con el motivo. El gate `audit` los ignora; cualquier aviso nuevo lo hace fallar.
