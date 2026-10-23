---
schema_version: 1
level: workspace
status: approved
last_reviewed: 2026-10-23
---

# Standards

The Reviewer enforces only what is written here (plus the spec, the contract and security.md).

## Design principles

| ID | Principle | Concrete rule for this stack |
|---|---|---|
| DP-1 | Seguridad por defecto | La entrada se valida con Pydantic en `http` antes de llegar al caso de uso; `Información restringida.md` (y cualquier documento marcado `CONFIDENCIAL`) no se indexa; ningún texto de documento se trata como instrucción. |
| DP-2 | Calidad | Toda respuesta `Exitosa` cita al menos una fuente existente; sin coincidencia suficiente el estado es `Sin información suficiente` con el mensaje fijo. |
| DP-3 | TDD | Prueba roja antes de cada comportamiento; los casos del entregable 7 son pruebas obligatorias. |
| DP-4 | Uso responsable de IA | Un modelo solo recibe fragmentos ya filtrados; su salida pasa por el guardrail de salida y debe citar fuentes recuperadas. |
| DP-5 | Mantenibilidad (SRP + DIP) | Un módulo, una responsabilidad; `aplicacion` depende de puertos de `dominio`, nunca de un adaptador concreto. |
| DP-6 | Optimización de costos | Sin coincidencia sobre el umbral no se llama al modelo; los embeddings son locales y se calculan una vez; al modelo se envían solo los fragmentos necesarios; sin clave, modo extractivo sin costo. |
| DP-7 | Observabilidad | Cada consulta se persiste y emite un log JSON con `requestId`, `estado` y `latenciaMs`. |
| DP-8 | ACID en escrituras | El registro de una consulta es una sola transacción: se guarda completo o no se guarda. |
| DP-9 | Simplicidad | No se crea una abstracción sin un segundo uso real o un requisito que la pida. |

## Principle precedence

1. The architecture explicitly chosen in `architecture.md`.
2. The framework conventions documented by the stack skill.
3. Generic principles only where the first two are silent.

Do not wrap a framework capability in a duplicate abstraction. Record architecture as a team choice;
never infer it from the framework.

## Conventions
- Backend: Python con tipado estático (mypy `strict = true`, MDO-0001 C-8) y formato/lint con ruff. Frontend:
  TypeScript `strict`. Nombres de dominio en español según `glossary.md`.
- Pruebas en `tests/` espejando `src/`: pytest para el backend, Vitest para el frontend.
- Las pruebas nunca llaman a Gemini ni descargan modelos: usan dobles de `Redactor` y de embeddings.
- Exemplar files (backend): puerto `src/server/dominio/puertos.py`; caso de uso
  `src/server/aplicacion/consultar.py`; ruta `src/server/http/rutas.py`; adaptador
  `src/server/infraestructura/persistencia/repositorio.py`; prueba unitaria
  `tests/server/aplicacion/test_consultar.py`; e2e `tests/server/e2e/test_flujo_consulta.py`. Frontend: OPEN.

## Errors
Códigos de `POST /api/consultar` (decisión del PE, 2026-10-23; intake Q-2, Q-6):

| Caso | Código |
|---|---|
| `Exitosa`, `Sin información suficiente` o `Bloqueada por seguridad`, también con la base documental vacía | 200 |
| Validación: pregunta vacía, de más de 1.000 caracteres o cuerpo inválido | 422 |
| Cuerpo mayor a 16 KB | 413 |
| Tipo de contenido distinto de JSON | 415 |
| Error inesperado | 500 |

Los errores siguen RFC 9457 (`application/problem+json`) con `requestId` y un mensaje legible; el 500
no expone detalles internos y queda en el log. Si Gemini falla, la respuesta es extractiva con 200. Un
error tragado es bloqueante.
Todo mensaje de error visible se fija con su texto exacto en la spec; nunca "un mensaje claro" (MDO-0001 CC-5).

## Logging
JSON estructurado. Nunca se registran secretos, credenciales, datos personales ni el contenido de
documentos confidenciales.

## Dependencies
Nuevas dependencias las aprueba el PE; solo licencias permisivas (MIT, Apache-2.0, BSD); versiones
fijadas en el lockfile. Para Gemini se usa `google-genai` (SDK oficial, `googleapis/python-genai`);
nunca `google-generativeai`, deprecado y sin soporte desde el 2025-11-30 (su página de PyPI).
Excepción (PE, 2026-10-23, MDO-0001): en dependencias transitivas sin modificar se aceptan MPL-2.0 y
PSF-2.0, y cualquier licencia igual o más permisiva que MIT (MIT-0, ISC, 0BSD, CC0-1.0, Unlicense).
Una premisa sobre límites de una API externa (plazos, cuotas, formatos) se verifica con una llamada real antes de aprobar el diseño (MDO-0001 CC-1).

## Clean-code thresholds (level 0 gates, blocking)

| Metric | Threshold | Tool |
|---|---|---|
| Cyclomatic complexity per function | ≤ 10 | ruff (backend); linter del frontend OPEN |
| Function length (lines) | ≤ 50 | linter |
| File length (lines) | ≤ 300 | linter |
| Duplication | sin bloques duplicados > 10 líneas | revisión |
| Layer-violating imports | none | revisión / regla de lint |
| Dead code | none | typecheck + lint |

## Gates
Backend: los de `projects[].gates` en `.mandao/config.yml` (format, lint, typecheck, test, secrets,
sast, audit y metrics = evals; MDO-0001 C-8). Frontend: OPEN hasta que exista `package.json`.
