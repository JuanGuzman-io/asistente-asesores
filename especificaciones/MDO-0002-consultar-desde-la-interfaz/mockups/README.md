---
schema_version: 1
source: design
link: https://claude.ai/artifact/7Q9xL9mv5eZJnwzdvkRFW3
artboard: 1 · Inicio (clic en el orbe)
files:
  - Main.html
  - Pensando.html
  - Respuesta.html
  - Oscuro.html
---

# Mockups — Bot-W, pantalla de consulta

Exportación a HTML independiente del canvas de Claude Design aprobado por el PE (C-5). Cada archivo se abre directo en el navegador, sin compilar y sin recursos externos (usa Geist si está instalada; si no, la fuente del sistema). En `Main.html` y `Oscuro.html`, un clic en el orbe alterna entre reposo y escuchando.

| File | Screen or state | AC |
|---|---|---|
| Main.html | Inicio claro: orbe animado, saludo, caja de pregunta y tres sugerencias sobre fondo degradado de Banco W | AC-1 |
| Pensando.html | Consulta en proceso: burbuja del asesor, orbe con pulsos, estado y líneas de carga | AC-1 |
| Respuesta.html | Respuesta con estado y fuente citada; caja fija abajo para otra pregunta | AC-1 |
| Oscuro.html | Inicio en modo nocturno (`prefers-color-scheme: dark`): aurora, cuadrícula y orbe con resplandor | AC-1 |

Starting points: paleta de Banco W de `src/web/src/estilos.css` (turquesa `#00b1bb`, morado `#5f259f`, naranja `#ff6900`), Geist y Geist Mono, y la referencia visual del PE (pestaña nueva de navegador con orbe centrado sobre la caja de entrada).
Deliberate differences from the existing UI: nombre de marca Bot-W; sin panel lateral; fondo con degradado animado (antes, fondos planos); orbe animado como protagonista; preguntas sugeridas que llenan la caja sin enviar (C-5). El estado de error (AC-2) no tiene pantalla propia en el mock: usa la misma burbuja del asistente con el estilo de alerta.
