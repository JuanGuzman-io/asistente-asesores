---
schema_version: 1
spec: MDO-0002-consultar-desde-la-interfaz
---

# Quickstart — Consultar desde la interfaz

**Before you start:** el backend de MDO-0001 corriendo en el puerto 8000 según el README, y `npm ci` hecho en `src/web`.

1. En `src/web`, ejecuta `npm run dev` y abre la dirección que imprime (por defecto `http://localhost:5173`).
   You should see: el campo "Pregunta" y el botón "Consultar".
2. Escribe "¿Cuál es el monto máximo del Crédito Productivo Impulso?" y pulsa "Consultar".
   You should see: "Procesando consulta…" y el botón deshabilitado; luego la respuesta con $50.000.000, el estado "Exitosa" y la fuente "Productos de Crédito > Crédito Productivo Impulso" con su fragmento.
3. Cambia la pregunta por "¿Va a llover mañana en Bogotá?" y consulta.
   You should see: "No tengo información suficiente para responder.", el estado "Sin información suficiente" y "Sin fuentes".
4. Borra la pregunta, escribe solo espacios y consulta.
   You should see: un error claro con "Código de referencia: …", y los espacios siguen en el campo.
5. Detén el backend y consulta otra vez.
   You should see: "No se pudo conectar con el servicio. Verifica que esté en ejecución."

**Expected result:** el asesor consulta desde la pantalla, ve el estado de procesamiento, la respuesta con sus fuentes y su estado, y un error claro cuando algo falla.
