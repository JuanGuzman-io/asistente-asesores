---
schema_version: 1
level: workspace
status: approved
last_reviewed: 2026-10-23
asvs_level: 1
---

# Security

## Data classification

| Class | Examples | Rules |
|---|---|---|
| Public | — | — |
| Internal | `Data/Productos de Crédito.md`, `Portafolio de Microseguros.md`, `Procedimientos Operativos.md`, `Políticas de Atención.md`, `Manual del Asesor Comercial.md` | Consultables por asesores; se citan como fuente. |
| Confidential | `Data/Información restringida.md` (sistema interno, token, usuario, clave temporal) | Nunca se indexa, nunca aparece en una respuesta, un prompt o un log. |
| Personal data | Datos de clientes que un asesor escriba en una pregunta | Nunca se registran en logs; la pregunta se guarda solo en la base local de consultas. |

Ningún servidor de desarrollo sirve la raíz del repositorio; `Data/` va en su lista de denegación (MDO-0002 T1 F1).

## Authentication and authorization
Fuera del alcance de la prueba (ejecución local de un solo usuario). ASSUMPTION(source: PDF, entregable 6):
sin autenticación; en producción se exigiría SSO corporativo (ver cuestionario).

## Secrets
No hay secretos en el código. `GEMINI_API_KEY` vive en `.env` (ignorado por git) y se documenta en
`.env.example` sin valor. Nunca se registra en logs ni se devuelve al frontend.

## Data sent to the model provider
- A Gemini solo se envían la pregunta (después del guardrail de entrada) y los fragmentos recuperados de
  documentos internos. Nunca información confidencial, credenciales ni datos de otras consultas.
- **Nivel gratuito de la Gemini API:** el contenido se usa para mejorar los productos de Google
  (https://ai.google.dev/gemini-api/docs/pricing, leído 2026-10-23). Se acepta solo porque la base
  documental es irreal (PDF p. 2). Con datos reales o datos personales en las preguntas, el nivel pago
  es obligatorio (allí el contenido no se usa para mejorar productos).

## Threat model (light)

| Asset | Threat | Mitigation | Owner |
|---|---|---|---|
| Información confidencial | Una pregunta pide credenciales, tokens, configuraciones internas o "información restringida" | Guardrail de entrada por reglas, categoría `informacion_restringida` → `Bloqueada por seguridad`; el documento no está indexado | Backend |
| Datos de clientes | Una pregunta pide datos de otro cliente o de uno identificado (BR-4, BR-8) | Guardrail de entrada, categoría `datos_de_clientes` → `Bloqueada por seguridad`; la base no tiene datos de clientes | Backend |
| Comportamiento del asistente | Prompt injection en la pregunta ("ignora tus instrucciones…") | Guardrail de entrada, categoría `prompt_injection`; la pregunta nunca se concatena como instrucción | Backend |
| Comportamiento del asistente | Instrucción embebida en un documento (p. ej. la de `Información restringida.md`) | Los documentos son datos; los confidenciales no se indexan; guardrail de salida | Backend |
| Respuesta | El modelo opcional inventa o filtra datos | Guardrail de salida: solo fuentes recuperadas, sin patrones de credenciales | Backend |
| Disponibilidad | Consultas extensas | Límite de longitud validado en entrada (ver `performance.md`) | Backend |

El guardrail de entrada (`src/server/dominio/guardrail_entrada.py`, MDO-0003 D2) son reglas deterministas
sobre el texto normalizado, evaluadas antes de buscar; el mensaje de bloqueo es fijo y la categoría va
solo en el log. Limitación aceptada: no detecta ofuscación (letras separadas, homoglifos, idiomas distintos
del español y el inglés) ni un cliente nombrado sin tratamiento ni número; la cubren el índice sin
confidenciales ni datos de clientes, el prompt que trata la pregunta como datos y el guardrail de salida.
