---
schema_version: 1
level: workspace
status: approved
last_reviewed: 2026-10-23
---

# UX

## Principles
- La interfaz permite realizar consultas y ver la respuesta, sus fuentes, los errores y el estado de
  procesamiento (PDF, entregable 6).
- El estado de la respuesta (`Exitosa`, `Sin información suficiente`, `Bloqueada por seguridad`) siempre
  es visible y distinguible.
- Textos en español, claros y sin jerga técnica.
- El diseño visual no se evalúa: componentes nativos de HTML, sin librería de UI.
- Marca **W+IA** (PE, MDO-0002 C-7; renombrada desde Bot-W): orbe animado sobre la caja de pregunta, fondo
  con degradado de los colores de Banco W y modo nocturno por `prefers-color-scheme: dark`, según el mock
  `especificaciones/MDO-0002-consultar-desde-la-interfaz/mockups/`. Toda animación vive bajo
  `prefers-reduced-motion: no-preference`.

## Design tokens
Paleta de Banco W en `:root` de `src/web/src/estilos.css` (MDO-0002 C-6), con modo oscuro y contraste AA.
La fuente de verdad es ese archivo; los valores de texto y fondo cambiaron desde la spec (`#1b1b1b`,
`#faf9f6`) en el pase visual de W+IA:

| Token | Valor | Uso |
|---|---|---|
| Turquesa | `#00b1bb` | Color principal, junto con el naranja |
| Naranja | `#ff6900` | Acento principal |
| Morado | `#5f259f` | Solo acompaña: fondo degradado y orbe |
| Texto | `#14161a` | Texto y botón principal |
| Fondo | `#f6f7fb` | Fondo claro |
| Acento de texto | `#00737a` | Turquesa oscurecido para texto y foco (contraste AA) |

## Accessibility target
ASSUMPTION: WCAG 2.1 AA básico (etiquetas en formularios, foco visible, contraste del navegador).
