---
schema_version: 1
level: workspace
status: approved
last_synced: 2026-10-23
owner: PE
---

# Product

Fuente: *Prueba técnica — Desarrollador de IA* (PDF, 8 páginas, leído 2026-10-23) y la base documental
de `Data/`. El backend de consulta (MDO-0001) está implementado; las demás capacidades siguen planeadas.

## Vision
Un asistente interno que responde a los asesores comerciales, con información oficial y citando su
fuente, consultas sobre productos de crédito, microseguros, procedimientos operativos y políticas internas.

## Users and roles
- **Asesor comercial:** hace consultas y recibe respuestas con sus fuentes.
- **Responsable de la base documental:** mantiene los documentos de `Data/`. ASSUMPTION: sin interfaz;
  edita los archivos.

## Scope
- **Dentro:** consultas en lenguaje natural; respuesta solo con información encontrada; citas de
  fuentes; registro de cada consulta con su estado; frontend local.
- **Fuera:** autenticación, despliegue, gestión de clientes, edición de documentos desde la interfaz.

## Restricciones de entrega
Condiciones de la entrega de la prueba, no reglas de comportamiento del asistente.

| ID | Restricción | Source | Date |
|---|---|---|---|
| DC-1 | La base documental de ejemplo puede ampliarse con los registros que se consideren necesarios; los archivos finales de `Data/` (los seis, incluido `Políticas de Atención.md`) forman parte de los entregables. | PDF p. 2 | 2026-10-23 |
| DC-2 | Entrega en repositorio GitHub, máximo 72 horas; se permite el uso de IA y no se requieren herramientas pagas. | PDF p. 1 | 2026-10-23 |

## Capability map

| Capability | Evidence in code | Documented in | Status |
|---|---|---|---|
| Responder consultas con fuentes | `src/server/aplicacion/consultar.py`, `src/server/http/rutas.py` (MDO-0001) | PDF p. 2, p. 5 | implemented |
| Indicar falta de información | `src/server/dominio/reglas.py` (`MENSAJE_SIN_INFORMACION`, MDO-0001) | PDF p. 5; Manual del Asesor, "Casos Especiales" | implemented (frase del PDF, ver BR-3) |
| Bloquear consultas sobre información restringida | — | PDF p. 2; Información restringida.md | planned |
| Registrar consultas (pregunta, fecha y hora, respuesta, fuentes, estado) | `src/server/infraestructura/persistencia/repositorio.py` (MDO-0001) | PDF p. 2 | implemented |
| Frontend para consultar y ver respuesta, fuentes, errores y estado | `src/web/src/App.tsx`, `src/web/src/Resultado.tsx`, `src/web/src/api.ts` (MDO-0002) | PDF p. 5 | implemented |
