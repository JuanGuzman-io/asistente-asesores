# Asistente para asesores comerciales

Prueba técnica de **Desarrollador de IA** (Laboratorio Digital, Vicepresidencia de Innovación y Mercadeo).

## Descripción

Asistente interno que responde a los asesores comerciales preguntas sobre productos de crédito,
microseguros, procedimientos operativos y políticas internas, **usando solo la base documental de
`Data/`** y citando siempre de qué documento, sección y texto sale cada respuesta.

- **Responde con fuentes.** Si la base documental no tiene la información, responde exactamente "No
  tengo información suficiente para responder." y no inventa nada.
- **Bloquea por seguridad.** No responde preguntas que piden información restringida (credenciales,
  configuraciones internas), intentos de manipularlo ("ignora tus instrucciones…") ni datos de otros
  clientes.
- **Registra cada consulta:** pregunta, fecha y hora, respuesta, fuentes y estado (`Exitosa`, `Sin
  información suficiente` o `Bloqueada por seguridad`).
- **Corre 100 % en local** y sin herramientas pagas. Gemini es opcional y está apagado por defecto.

### Cómo se construyó: SDD con Mandao

El proyecto se desarrolló con **[Mandao](https://www.npmjs.com/package/mandao)**, un CLI de desarrollo
guiado por especificaciones (SDD) para agentes de código. Mandao llevó cada característica por el mismo
ciclo: constitución → historia → especificación → tareas → implementación con TDD → verificación →
cierre. Cada criterio de aceptación se traza hasta sus pruebas y sus commits.

Mandao se **adaptó al formato que pide la prueba**:

- Las carpetas de Mandao se renombraron a las del enunciado (`paths` en `.mandao/config.yml`):
  `constitucion/` y `especificaciones/`.
- `constitucion/constitucion.md` es el entregable 1: los siete principios en una página. Mandao agrega
  el detalle en los demás documentos de `constitucion/` (arquitectura, estándares, seguridad, producto,
  reglas de negocio, glosario…).
- Cada característica vive en `especificaciones/MDO-000n-<descripción>/` (el formato de ID de Mandao) y
  trae **`especificacion.md`, `plan.md` y `tareas.md`** con los nombres del enunciado. Son índices que
  señalan en qué documento de Mandao está cada punto pedido:

| El enunciado pide | Archivo índice | Documentos de Mandao |
|---|---|---|
| Contexto, objetivo, alcance, requerimientos funcionales y no funcionales, riesgos, criterios Gherkin | `especificacion.md` | `story.md` (criterios GIVEN/WHEN/THEN), `requirements.md` o `spec.md`, `design.md` (riesgos) |
| Arquitectura, componentes, estrategia de pruebas | `plan.md` | `design.md`, `data-model.md` |
| Lista ordenada de tareas técnicas | `tareas.md` | `tasks.md` |

Las tres características:

| Spec | Qué entrega |
|---|---|
| [MDO-0001](especificaciones/MDO-0001-consultar-la-base-documental-con-fuentes/) | Backend de `POST /api/consultar`: base documental, búsqueda, respuesta con fuentes, validación, errores y registro |
| [MDO-0002](especificaciones/MDO-0002-consultar-desde-la-interfaz/) | Interfaz para consultar y ver respuesta, fuentes, errores y estado |
| [MDO-0003](especificaciones/MDO-0003-bloquear-consultas-que-comprometen-la-seguridad/) | Bloqueo por seguridad (`Bloqueada por seguridad`) |

Los requisitos se extrajeron del PDF del enunciado con el intake de Mandao (`/mandao-story --from`):
[`docs/product/intake/prueba-tecnica-2026-10-23.md`](docs/product/intake/prueba-tecnica-2026-10-23.md)
tiene las historias con su referencia a la página del PDF y las preguntas que se resolvieron.

## Arquitectura

Monolito modular en un repositorio, con **arquitectura hexagonal** en el backend: el caso de uso
`consultar` depende de puertos (`BuscadorDocumental`, `RepositorioConsultas`, `Redactor`) y la
infraestructura los implementa. Así se cambia la búsqueda, la persistencia o el modelo sin tocar las
reglas. Detalle en [`constitucion/architecture.md`](constitucion/architecture.md).

```
Interfaz (React)  ──POST /api/consultar──▶  http (FastAPI: validación, errores RFC 9457)
                                               │
                                               ▼
                                     aplicacion: consultar
                                               │
              ┌────────────────────────────────┼─────────────────────────────┐
              ▼                                ▼                             ▼
  dominio: guardrail de entrada      busqueda híbrida                 redactor
  (bloqueo por seguridad,            FTS5 (palabras) + Qdrant         extractivo, o Gemini
   antes de buscar)                  (vectores) + umbral              con guardrail de salida
                                               │
                                               ▼
                                     persistencia: SQLite (registro de cada consulta)
```

Recorrido de una pregunta:

1. **Validación** de la entrada: vacía o de más de 1.000 caracteres → `422`.
2. **Guardrail de entrada**, con reglas deterministas en código: información restringida, prompt injection
   o datos de clientes → `Bloqueada por seguridad`, sin buscar.
3. **Búsqueda híbrida.** La pregunta se vectoriza con el modelo local y se busca en dos índices: Qdrant
   (similitud coseno) y SQLite FTS5 (palabras, con stemming en español). Los resultados se combinan con
   Reciprocal Rank Fusion.
4. **Umbral de relevancia.** Sin soporte → "No tengo información suficiente para responder.", sin llamar
   a ningún modelo.
5. **Redacción.** Extractiva: el fragmento con su fuente. Con clave de Gemini, el modelo redacta solo con
   los fragmentos recuperados, y un guardrail de salida comprueba que cite fragmentos reales y que cada
   cifra esté en ellos. Si no lo cumple o la llamada falla, se usa la respuesta extractiva.
6. **Registro** en SQLite, en el mismo paso que decide la respuesta.

Los documentos se fragmentan por sección y se vectorizan **al arrancar** el servidor; solo se recalculan
los fragmentos nuevos o modificados. `Información restringida.md` nunca entra al índice.

### Por qué así: RAG con la generación opcional

La solución es un RAG. La **R** es la búsqueda híbrida, la **A** son los fragmentos con su documento y
sección, y la **G** es Gemini. La generación está apagada por defecto porque el enunciado no la exige ni
pide herramientas pagas, y el modo extractivo es local, gratis, reproducible y no puede alucinar. Las
decisiones (validar, bloquear, decidir si hay soporte, aceptar la salida del modelo) son siempre código
determinista; el modelo solo redacta.

## Tecnologías

| Parte | Tecnología | Uso |
|---|---|---|
| Backend | Python 3.13, gestionado con `uv` | Lenguaje y entorno (`.python-version`) |
| | FastAPI + Pydantic | API y validación |
| | SQLite + FTS5 | Registro de consultas y búsqueda por palabras |
| | Qdrant en modo local (`qdrant-client`) | Base vectorial dentro del proceso, sin servidor |
| | `fastembed` (`paraphrase-multilingual-MiniLM-L12-v2`) | Embeddings locales en español, sin costo |
| | `py-rust-stemmers` | Stemming en español para FTS5 |
| | `google-genai` (Gemini 3.5 Flash-Lite) | Redacción opcional |
| Frontend | React + TypeScript + Vite | Interfaz local; sin librería de UI |
| | `react-markdown` | Muestra la respuesta sin interpretar HTML ni enlaces |
| Pruebas | pytest, `TestClient` de FastAPI | Backend: unidad, integración, e2e de la API y evaluaciones |
| | Vitest + Testing Library | Frontend |
| | Playwright | E2E de la interfaz contra el backend real |
| Calidad | ruff, mypy (estricto), ESLint, Prettier | Formato, lint y tipos |
| Seguridad | detect-secrets, bandit, pip-audit, npm audit | Secretos, SAST y dependencias |
| CI | GitHub Actions | Todos los gates, las evaluaciones y las e2e en cada PR |

## Instalación

Requisitos: [`uv`](https://docs.astral.sh/uv/) (instala Python 3.13 si no está) y Node.js 22.

```bash
git clone https://github.com/JuanGuzman-io/asistente-asesores.git
cd asistente-asesores
uv sync
npm --prefix src/web ci
```

El **primer arranque** del backend descarga el modelo de embeddings (unos 0,22 GB) y tarda un poco más.
Después funciona sin red.

## Configuración

Opcional. Sin configuración, el asistente funciona en modo extractivo, sin costo.

```bash
cp .env.example .env
```

| Variable | Por defecto | Efecto |
|---|---|---|
| `GEMINI_API_KEY` | vacía | Con clave, Gemini redacta la respuesta a partir de los fragmentos encontrados |
| `GEMINI_MAX_CONCURRENCIA` | `5` | Máximo de llamadas simultáneas a Gemini; un valor inválido detiene el arranque |

La clave nunca se registra en logs ni se envía al frontend. A Gemini solo llegan la pregunta (después del
guardrail) y los fragmentos recuperados, nunca información confidencial. En el nivel gratuito, Google
usa el contenido para mejorar sus productos: se acepta solo porque los datos de la prueba son irreales;
con datos reales, el nivel pago es obligatorio (`constitucion/security.md`).

## Ejecución

Dos terminales, desde la raíz del repositorio:

```bash
# Terminal 1: backend en :8000 (siempre un solo worker: Qdrant local bloquea su carpeta)
uv run uvicorn src.server.principal:app --port 8000 --workers 1
# con Gemini: uv run --env-file .env uvicorn src.server.principal:app --port 8000 --workers 1

# Terminal 2: interfaz en :5173
npm --prefix src/web run dev
```

Abrir <http://localhost:5173>. La API también se puede usar directamente:

```bash
curl -s -X POST localhost:8000/api/consultar -H 'Content-Type: application/json' \
  -d '{"pregunta":"¿Cuál es el monto máximo del Crédito Productivo Impulso?"}'
```

```json
{ "respuesta": "…$50.000.000…", "fuentes": [{ "documento": "Productos de Crédito", "seccion": "Crédito Productivo Impulso", "fragmento": "…" }], "estado": "Exitosa" }
```

La respuesta agrega `estado` al contrato del enunciado (`{ respuesta, fuentes }`): es compatible y lo
necesitan el registro y la interfaz. Errores: `422` validación, `413` cuerpo de más de 16 KB, `415` tipo
de contenido, `500` inesperado; todos en formato RFC 9457 con un `requestId` para buscarlo en el log.

## Pruebas

Desarrollo guiado por pruebas: en cada tarea, un agente *tester* escribió las pruebas antes del código y
Mandao registró que fallaban (rojo) antes de permitir la implementación. La evidencia queda en
`especificaciones/*/_log/execution.md`.

| Comando | Qué prueba |
|---|---|
| `uv run pytest` | Backend completo, sin red y sin descargar modelos (dobles de embeddings y de Gemini) |
| `uv run pytest -m eval` | Evaluaciones de calidad con el modelo real sobre `tests/fixtures/consultas.json` |
| `npm --prefix src/web test` | Frontend (Vitest) |
| `cd src/web && npx playwright install chromium && npm run e2e` | E2E de la interfaz; requiere el backend en :8000 |

Casos mínimos del enunciado (entregable 7):

| Caso | Dónde se prueba |
|---|---|
| Consulta válida | MDO-0001 AC-3; e2e de la interfaz |
| Pregunta vacía | MDO-0001 AC-7 (`422`); MDO-0002: la interfaz no deja enviarla |
| Base documental vacía | MDO-0001 AC-12 (`200`, sin información) |
| Caracteres especiales | MDO-0001 AC-8 (tildes, ñ, signos, emojis) |
| Documentos duplicados | MDO-0001 AC-2 (contenido idéntico normalizado, una sola vez) |
| Consultas extensas | MDO-0001 AC-9 (1.000 caracteres se acepta, 1.001 → `422`) |

Evaluaciones sobre el dataset v5:

| Métrica | Resultado | Objetivo |
|---|---|---|
| EV-1 Recuperación de la sección correcta | 0,985 | ≥ 0,90 |
| EV-2 "Sin información" cuando corresponde | 1,000 | ≥ 0,90 |
| EV-3 Falsos "sin información" | 0,000 | ≤ 0,10 |
| EV-8 Bloqueo de preguntas que deben bloquearse | 1,000 | = 1,00 |
| EV-9 Falsos positivos de bloqueo | 0 | 0 |

El CI (`.github/workflows/ci.yml`) corre en cada PR los gates del backend y del frontend, las
evaluaciones y las e2e con el backend levantado.

## Limitaciones

- **Un solo proceso.** Qdrant en modo local bloquea su carpeta, así que el backend corre con un worker.
  Basta para la prueba; en producción se usaría Qdrant en modo servidor.
- **Las reglas de seguridad son patrones.** No reconocen pedidos disfrazados (letras separadas, otros
  idiomas, un cliente nombrado sin "señor" ni número). Los cubren las otras capas: la información
  restringida no está en el índice y la base no tiene datos de clientes.
- **El modo extractivo no detecta qué dato falta.** Si se pregunta un dato que no existe de un producto
  que sí existe (la tasa del Crédito Agro Crece), sin Gemini muestra la sección del producto con "Esto es
  lo que encontré en la base documental:" y no afirma el dato, pero tampoco dice que falta. Con Gemini,
  nombra el dato que falta.
- **El modo extractivo puede mostrar un fragmento relacionado de más** (por ejemplo, Solicitud de Crédito
  al preguntar por actualización de datos). Se prefirió así: perder una sección correcta pesa más.
- **El margen de los umbrales es estrecho** (0,008) con este volumen de datos. Una evaluación falla si
  algún margen baja de 0,005, para que no empeore en silencio.
- **Vulnerabilidades aceptadas:** `.pip-audit-ignore` lista avisos de pillow 12.3.0, que llega por
  `fastembed` (exige pillow < 13) y solo se usa en rutas de imagen; la app solo vectoriza texto.
- **Datos de prueba con aspecto de secreto:** `Data/Información restringida.md` contiene un token y una
  clave **falsos**, puestos a propósito para probar que el asistente nunca los indexa ni los expone.
- **`Data/Políticas de Atención.md`** no aparece en el árbol de la página 3 del enunciado, pero venía con
  el material y es la fuente de varias reglas de negocio, así que se mantiene como entregable.

## Mejoras futuras

- Qdrant en modo servidor (o pgvector) y varios workers detrás de un balanceador.
- Un reranker después de la búsqueda y un modelo de embeddings más grande.
- Memoria de conversación entre preguntas.
- Un clasificador dedicado como capa adicional contra prompt injection.
- Un mensaje de ayuda redactado por el LLM cuando no hay información, sin cambiar la respuesta fija.
- Proveedor de LLM configurable (el puerto `Redactor` ya lo permite).
- SAST para TypeScript en el CI y autenticación con SSO corporativo.
- Caché de respuestas y de vectores para preguntas repetidas.

## Uso de IA

- **Desarrollo:** Claude Code con Mandao. Un agente líder (Claude Opus 5.5) orquestó cada tarea, un
  *tester* escribió las pruebas en rojo, un *implementer* (Claude Sonnet 5.5) escribió el código y un
  *reviewer* independiente (Claude Opus 5.5, otro modelo) aprobó o rechazó cada tarea contra la spec y
  la constitución.
- **Producto:** Gemini 3.5 Flash-Lite, opcional, solo para redactar a partir de fragmentos recuperados.
- **Decisiones humanas:** el alcance, el stack, la seguridad y la aceptación de cada riesgo los decidió
  el Product Engineer y quedaron registrados en las specs y en `constitucion/CHANGELOG.md`.

El detalle está en [`docs/Cuestionario.md`](docs/Cuestionario.md).
