---
schema_version: 1
level: workspace
status: approved
last_reviewed: 2026-10-23
owner: PE
---

# Constitución — Asistente para asesores comerciales

Principios que guían el desarrollo. Cada uno tiene su regla verificable en `standards.md` (DP-*) y su
detalle en el documento indicado. Fuente: *Prueba técnica — Desarrollador de IA*, entregable 1.

1. **Seguridad por defecto (DP-1).** Todo se niega salvo que esté permitido: la entrada se valida antes
   de procesarla, la información confidencial (`Data/Información restringida.md`) nunca entra al índice
   consultable, y los documentos son datos, nunca instrucciones. Una consulta que pide información
   restringida o intenta cambiar el comportamiento termina en `Bloqueada por seguridad`. → `security.md`
2. **Calidad (DP-2).** Una respuesta solo usa información encontrada en la base documental y siempre
   cita sus fuentes; sin soporte, responde que no tiene información suficiente. Lint, tipos y pruebas
   son gates bloqueantes. → `standards.md`
3. **TDD (DP-3).** Cada comportamiento empieza con una prueba que falla: casos positivos, negativos y
   borde del entregable 7 (pregunta vacía, base vacía, caracteres especiales, documentos duplicados,
   consultas extensas). Sin prueba roja no hay implementación. → `standards.md`
4. **Uso responsable de IA (DP-4).** La IA asiste; no decide sola. Un modelo, si se usa, solo redacta a
   partir de fragmentos recuperados, nunca ve información confidencial y su salida se valida (fuentes
   citadas, sin datos restringidos). Las decisiones de seguridad y de negocio son código determinista
   y revisado por personas. → `model-registry.md`, `architecture.md`
5. **Mantenibilidad (DP-5).** Módulos con una sola responsabilidad que se comunican por contratos; el
   caso de uso depende de puertos, no de proveedores (búsqueda, persistencia, modelo). Lo más simple que
   funcione: sin abstracciones que nadie pidió. → `architecture.md`
6. **Optimización de costos (DP-6).** El modo por defecto corre local y sin servicios pagos; un modelo
   externo es opcional, se activa por configuración y solo recibe los fragmentos necesarios. Se cachea
   lo determinista (índice, respuestas a preguntas repetidas). → `performance.md`
7. **Observabilidad (DP-7).** Cada consulta queda registrada (pregunta, fecha y hora, respuesta, fuentes,
   estado) y emite un log estructurado con id de solicitud, estado y latencia, sin secretos ni datos
   personales. → `infrastructure.md`

Precedencia: la arquitectura elegida en `architecture.md`, luego las convenciones documentadas del
framework, y los principios genéricos solo donde las dos primeras callan.
