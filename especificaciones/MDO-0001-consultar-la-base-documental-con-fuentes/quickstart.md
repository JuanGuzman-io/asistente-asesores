---
schema_version: 1
spec: MDO-0001-consultar-la-base-documental-con-fuentes
---

# Quickstart — Consultar la base documental con fuentes

**Before you start:** `uv sync`, el servidor corriendo con `uv run uvicorn src.server.principal:app --port 8000 --workers 1` hasta ver `Application startup complete.` (sin `GEMINI_API_KEY` responde en modo extractivo) y `curl`.

1. `curl -s -X POST localhost:8000/api/consultar -H 'Content-Type: application/json' -d '{"pregunta":"¿Cuál es el monto máximo del Crédito Productivo Impulso?"}'`
   You should see: `estado` "Exitosa", una respuesta con $50.000.000 y una fuente "Productos de Crédito" / "Crédito Productivo Impulso" con su fragmento.
2. Repite con `{"pregunta":"¿Va a llover mañana en Bogotá?"}`.
   You should see: "No tengo información suficiente para responder.", `fuentes` vacío y `estado` "Sin información suficiente".
3. Repite con `{"pregunta":"   "}`.
   You should see: código 422 y un JSON de error con `detail` y `requestId`.
4. Repite la pregunta del paso 1 con `-H 'Content-Type: text/plain'`.
   You should see: código 415.
5. Pregunta por "token interno" o "clave temporal".
   You should see: el mensaje fijo de falta de información; nada de `Información restringida.md` aparece.

**Expected result:** el asesor obtiene respuestas con su fuente solo cuando la base documental las sustenta, y un mensaje claro en los demás casos.
