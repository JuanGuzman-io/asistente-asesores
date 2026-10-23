---
schema_version: 1
spec: MDO-0003-bloquear-consultas-que-comprometen-la-seguridad
environments: []
published: []
applied:
  - constitucion/critical-flows.md
  - constitucion/business-rules.md
  - constitucion/security.md
  - constitucion/model-registry.md
  - constitucion/glossary.md
  - constitucion/CHANGELOG.md
closed_at: 2026-10-23T23:48:20.193Z
---

# Close — MDO-0003-bloquear-consultas-que-comprometen-la-seguridad

El asistente bloquea, antes de buscar, las consultas que piden información restringida o datos de otros
clientes y las que intentan cambiar su comportamiento: responde un mensaje fijo con estado `Bloqueada por
seguridad` y registra la categoría en el log. Las preguntas legítimas con palabras sensibles no se bloquean.

## Outcome

- AC-1: met (T1, T2, T4 committed; verify PASS)
- AC-2: met (T1, T2, T4 committed; verify PASS)
- AC-3: met (T1, T2, T3, T4 committed; verify PASS)
- AC-4: met (T1, T2, T4 committed; verify PASS)

## For the PO

El asesor ya no puede obtener del asistente credenciales, configuraciones internas, la información
restringida ni datos de otros clientes, y un intento de "ignora tus instrucciones" tampoco funciona: en
todos esos casos recibe el mismo mensaje, "No puedo responder esta consulta porque no cumple las políticas
de seguridad de la información.", sin que se diga qué regla se activó. Cada bloqueo queda registrado y el
registro técnico dice de qué tipo fue, sin guardar ahí la pregunta. Preguntas legítimas como "¿Qué hago si
un cliente olvida su clave?" o "¿Qué cubre Negocio Seguro?" siguen respondiéndose, y las preguntas fuera de
tema siguen diciendo que no hay información suficiente. La interfaz ya mostraba este estado: no cambió.

Pendiente: el README (intake I-9) debe contar la limitación de las reglas fijas: no reconocen pedidos
disfrazados (letras separadas, otros idiomas distintos del inglés, un cliente nombrado sin "señor" ni
número). Esos casos los cubren las otras protecciones: la información restringida no está en la base y la
base no tiene datos de clientes.

## For developers

- **`dominio`:** `guardrail_entrada.py` con `normalizar` (NFKD sin marcas, `casefold`, espacios
  colapsados) y `evaluar_entrada`, tres familias de expresiones en orden fijo (`prompt_injection`,
  `informacion_restringida`, `datos_de_clientes`), ventanas tolerantes a puntuación
  `(?:\W+\w+){0,n}\W+` y las excepciones estrechas de AC-4 escritas en [design.md D2](design.md#d2).
  `CategoriaBloqueo` en `estados.py`, `MENSAJE_BLOQUEO` en `reglas.py`, `Resultado.categoria` opcional.
- **`aplicacion`:** `consultar` evalúa el guardrail antes del buscador; un bloqueo no llama a buscador ni
  redactor, se registra con modo `ninguno` y, si el registro falla, el error se propaga (D1, D5).
- **`http`:** la ruta pasa la categoría a `request.state`; el middleware la entrega a `registrar_peticion`,
  que agrega `categoria` a la línea JSON solo en bloqueos. El contrato de `POST /api/consultar` no cambió.
- **Datos de prueba:** `tests/fixtures/consultas.json@v5` con tipos `bloqueada` (25 preguntas, al menos 6
  por categoría) y `sensible`; EV-8 y EV-9 corren sin modelo en la suite normal y por HTTP en `-m eval`.
- **Cambios de plan durante implement:** T2 absorbió la actualización de pruebas y evals existentes que el
  bloqueo rompía (CC-1, CC-2); T4 absorbió NFR-2 sobre todo el dataset. `.mandao/config.yml` define
  `tests.impacted` del backend como `uv run pytest -q tests/server`, porque la selección por defecto le
  pasaba el JSON del dataset a pytest.
- **Diagrama:** el design no tenía diagrama aprobado (un paso nuevo en un flujo existente), así que no hay
  deriva que medir.
- **Cómo probar:** `uv run pytest -q tests/server`, `uv run pytest -m eval` y los pasos de
  [quickstart.md](quickstart.md).

## Kaizen

- **Medida:** 4 tareas, tasa de retrabajo 0,5, 3 FAIL del revisor (T1 dos, T4 uno), sin escalamientos ni
  pivotes; las 4 tareas con prueba roja antes del código. Costo equivalente 19,34 USD (implement 14,61, el
  líder 9,15). La comparación TDD vs. sin TDD tiene datos insuficientes (n = 2 y 0, mínimo 5).
- **Lección 1:** el segundo FAIL de T1 (F5) vino del brief de retrabajo del líder, que pidió quitar
  elementos de D2 para eliminar falsos positivos. Un brief de retrabajo cita la regla del design, y acotar
  una regla aprobada se escribe primero en `design.md`.
- **Lección 2:** CC-1 y CC-2 ya anunciaban en specify que el bloqueo rompía el dataset y una e2e, pero el
  plan dejó ese ajuste en T4; el gate de evals de T2 falló y hubo que mover archivos entre tareas. La tarea
  que cambia un comportamiento actualiza las pruebas y evals existentes que rompe.
- **Sesiones:** 24 pausas (mediana 0,9 min, 1 entre 5 y 60 min); turnos por tarea T1 13, T2 1, T3 0, T4 not
  measured; verify 10; close not recorded.

## Delivery

- Closed: 2026-10-23T23:48:20.193Z
- Applied: `constitucion/critical-flows.md`, `constitucion/business-rules.md`, `constitucion/security.md`, `constitucion/model-registry.md`, `constitucion/glossary.md`, `constitucion/CHANGELOG.md`
- [Verify report](verify-report.md)
- [Quickstart](quickstart.md)
