---
schema_version: 1
level: project
status: approved
last_reviewed: 2026-10-23
---

# Model, prompt and dataset registry

## Models
| Use | Model | Provider | Version pinned | Cost per 1k requests | Owner |
|---|---|---|---|---|---|
| Redacción de la respuesta | `gemini-3.5-flash-lite` | Google (Gemini API, SDK `google-genai`) | código de modelo estable (sin `-preview`) | ≈ USD 1,10 en nivel pago (estimación abajo); USD 0 en nivel gratuito | tech lead |
| Respaldo sin clave o con la API caída | extractivo (sin modelo) | — | — | USD 0 | tech lead |
| Embeddings de búsqueda | `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` (384 dim, 0,22 GB) | local (ONNX, `fastembed` 0.9.0) | nombre de modelo fijo en configuración | USD 0 | tech lead |

### Almacén de vectores
Qdrant en modo local (`qdrant-client` 1.20.0, `QdrantClient(path=…)`), una colección de fragmentos con
distancia coseno y 384 dimensiones; corre dentro del proceso del backend, sin servidor. Fuentes:
https://pypi.org/project/qdrant-client/ y README de qdrant-client (leídos 2026-10-23). Verificado en local
el 2026-10-23 con `uv` (Python 3.13.16 y 3.13.4): insertar y buscar un punto devolvió el fragmento correcto
(coseno 0,8157 frente a 0,2802). Cambiar de modelo de embeddings obliga a recrear la colección.

### Por qué Google (Gemini 3.5 Flash-Lite)
Fuentes: https://ai.google.dev/gemini-api/docs/pricing y https://ai.google.dev/gemini-api/docs/models
(ambas actualizadas el 2026-10-22, leídas el 2026-10-23).

1. **Se puede evaluar sin pagar.** El modelo tiene nivel gratuito en la Gemini API ("Free of charge"),
   coherente con "No se requiere el uso de herramientas pagas" (PDF p. 1). Sin clave, la solución sigue
   funcionando en modo extractivo.
2. **El tamaño justo para la tarea.** Redactar a partir de 1-3 fragmentos cortos ya recuperados no
   necesita un modelo de frontera. La documentación lo describe como "the fastest and most cost-effective
   3.5 model, for high-throughput execution" y lo recomienda para baja latencia y costo. Es estable (no
   preview) y Google lo recomienda para proyectos nuevos.
3. **Costo bajo y predecible a escala.** Nivel pago: USD 0,30 por millón de tokens de entrada y USD 2,50
   por millón de salida. Estimación: ~2.000 tokens de entrada (fragmentos + instrucciones) y ~200 de
   salida por consulta ≈ USD 0,0011 por consulta, ≈ USD 110 al día con 100.000 consultas (pregunta del
   cuestionario). Bajan con caché de respuestas repetidas y con menos fragmentos por consulta.
   Alternativa más barata en la misma familia: `gemini-3.1-flash-lite` (USD 0,25 / 1,50).
4. **Un camino claro a producción con gobierno de datos.** En el nivel pago, el contenido **no** se usa
   para mejorar los productos de Google; en el gratuito **sí** ("Content used to improve our products").
   Por eso la prueba usa el nivel gratuito solo con datos irreales, y producción exige nivel pago (ver
   `security.md`).

Riesgo: dependencia de un proveedor externo. Mitigación: el modelo está detrás del puerto `Redactor`
(cambiar de proveedor no toca el caso de uso) y existe el respaldo extractivo.

## Prompts
| Name | Path | Version | Used by | Eval dataset |
|---|---|---|---|---|
| Redactor con fuentes | `src/server/infraestructura/redactor/prompt.md` (por crear) | v1 | `Redactor` (Gemini) | `tests/fixtures/consultas.json` (por crear) |

## Datasets
| Name | Purpose | Version | Location | Contains personal data |
|---|---|---|---|---|
| Base documental | Fuente de las respuestas | v1 (datos irreales del PDF) | `Data/` | No |
| Casos de prueba de consultas | Validar respuestas, estados y fuentes | por crear | `tests/fixtures/` | No |
