# Cuestionario

## Herramientas utilizadas

- **Claude Code** como entorno de agentes, con [**Mandao**](https://www.npmjs.com/package/mandao) como
proceso de desarrollo guiado por especificaciones (SDD) y TDD. Mandao es un CLI de mi autoría
([github.com/JuanGuzman-io/mandao](https://github.com/JuanGuzman-io/mandao)); esta prueba fue también un
uso real de su versión beta, adaptada a la estructura que pide el enunciado. Lo que encontré en el
camino (pasos manuales, flujos que se podían simplificar) quedó registrado en el backlog de Mandao.
- **Modelos:** Claude Opus 5.5 (líder y revisor) y Claude Sonnet 5.5 (implementación y pruebas) para
desarrollar; Gemini 3.5 Flash-Lite como modelo opcional del producto.
- **Claude Design** para crear los mockups de la interfaz, exportados a HTML como referencia para la
implementación.
- **Stack:** Python 3.13 con `uv`, FastAPI, SQLite + FTS5, Qdrant en modo local, `fastembed`; React +
TypeScript + Vite; pytest, Vitest, Playwright; ruff, mypy, ESLint; detect-secrets, bandit, pip-audit;
GitHub Actions.

## Qué actividades delegué a la IA

- Leer el PDF del enunciado y proponer historias con criterios de aceptación y referencia a cada página
(`docs/product/intake/prueba-tecnica-2026-10-23.md`).
- Redactar los borradores de la constitución, las especificaciones, los diseños y las tareas.
- Generar los mockups de la interfaz en Claude Design a partir de mi referencia visual y de la paleta
de Banco W: inicio, consulta en proceso, respuesta con fuentes y modo oscuro.
- Escribir las pruebas antes del código (agente *tester*), implementar (agente *implementer*) y revisar
cada tarea contra la spec y la constitución (agente *reviewer*, con otro modelo que el implementador).
- Investigar versiones, licencias y documentación oficial de cada dependencia.
- Escribir el workflow de CI y los borradores de esta documentación.

## Qué actividades realicé manualmente

La IA escribió; yo decidí qué se construía, cómo y cuándo estaba bien. En concreto:

**Interpretación del enunciado y producto**

- Leí el PDF contra la base documental y resolví sus ambigüedades y contradicciones antes de
especificar. Las seis quedaron registradas con su decisión en la propuesta del intake:
  - **el mensaje de "sin información":** el PDF y el Manual del Asesor dan textos distintos; elegí el del
  PDF, porque es el contrato evaluado;
  - **el campo `estado` en la respuesta:** compatible con el contrato y necesario para el registro y la
  interfaz;
  - **el límite de 1.000 caracteres** y cómo se cuentan (puntos de código tras normalizar a NFC);
  - **qué consultas se bloquean,** en tres categorías, con su lista de falsos positivos;
  - **mantener `Políticas de Atención.md`** aunque no aparezca en el árbol del enunciado;
  - **los códigos HTTP:** `422` para toda la validación, y RFC 9457.
- El LLM quedó opcional, porque el enunciado no lo exige, y dejé
como mejoras futuras el proveedor configurable y el mensaje de ayuda redactado por el modelo.

**Arquitectura y stack**

- Elegí el stack (Python con FastAPI, React con TypeScript) y la arquitectura hexagonal, con una regla
explícita: las decisiones son código determinista y el modelo solo redacta.
- Exigí una base vectorial real cuando la propuesta fue quitarla. Rechacé `sqlite-vec` cuando falló en
otro Python, y aprobé Qdrant en modo local solo después de verlo funcionar en dos versiones de Python.
- Elegí Gemini 3.5 Flash-Lite con su justificación de costo y de política de datos (nivel gratuito solo
con datos irreales).

**Calidad y seguridad**

- Exigí que todo se probara siempre: pruebas sin red en cada tarea y evaluaciones de calidad con el
modelo real como gate obligatorio, no opcional.
- Definí los gates (formato, lint, tipos, pruebas, secretos, SAST, auditoría y build) y acepté o rechacé
cada riesgo con su motivo: licencias de dependencias transitivas, vulnerabilidades de pillow no
alcanzables y el hueco de SAST en el frontend.
- Revisé los mensajes que ve el asesor y pedí cambios de experiencia que las pruebas no exigían: no
permitir enviar una pregunta vacía, un contador de caracteres y errores sin detalles internos.

**Diseño de la interfaz**

- Definí la referencia visual y aprobé los mockups generados en Claude Design: orbe centrado sobre la
caja de consulta, colores de Banco W y preguntas sugeridas que llenan la caja sin enviarla.
- Los [mockups exportados a HTML](../especificaciones/MDO-0002-consultar-desde-la-interfaz/mockups/)
quedaron versionados como referencia para implementar la interfaz.

**Verificación manual**

- Probé la aplicación en el navegador con una batería de preguntas: válidas, parafraseadas, con soporte
parcial, sin información, fuera de tema y de seguridad, incluidas preguntas legítimas con palabras
sensibles. Así encontré dos fallos de recuperación que las pruebas no cubrían: "¿Cuánto le prestan a un
pequeño comerciante?" (faltaba stemming en español) y "¿Qué dice la política de…?" (la decisión de
soporte). Los dos se corrigieron con prueba roja primero y se sumaron al dataset de evaluación.

**Orquestación y entrega**

- Coordiné varias sesiones de agentes en paralelo (backend, frontend, seguridad, CI y correcciones),
cada una en su rama. Ordené los merges y resolví sus cruces: la constitución compartida, la
configuración y el uso del puerto del backend.
- Ajusté el proceso para ganar velocidad sin quitar controles, por ejemplo evitando cortes de sesión
innecesarios entre tareas.
- Creé el repositorio, revisé los PRs, decidí el orden de merge y llevé el CI a verde en cada uno.

## Qué sugerencias rechacé de la IA

Algunas fueron propuestas directas de la IA; otras, opciones que me ofreció junto a su recomendación.
Las que descarté, y por qué:

**Arquitectura**

- **`sqlite-vec` como base vectorial.** La propuso la IA al definir la arquitectura. Cuando se verificó
en el entorno, no cargó en un Python sin soporte de extensiones de SQLite: un evaluador con ese Python
no podría arrancar el servidor. La cambié por Qdrant en modo local, verificado en dos versiones de
Python antes de aprobarlo.
- **Quitar la base vectorial** y calcular la similitud en memoria, como salida a ese problema. La
rechacé: con este volumen funcionaba, pero no muestra el camino hacia un RAG real.
- **Profundidad "lite" para la primera especificación,** que el flujo sugirió por defecto. Elegí la
profundidad estándar, porque el enunciado pide especificación y plan por separado, y el backend tenía
búsqueda, modelo y persistencia.

**Calidad de la búsqueda**

- **Recalibrar solo los umbrales** cuando las evaluaciones no llegaban a los objetivos. Los números
mostraban que las preguntas con y sin soporte se solapaban; en su lugar se incluyó el título de la
sección en lo que se vectoriza, y la separación mejoró de forma medible.
- **Sacar del dataset de evaluación las preguntas que fallaban.** Era la forma más rápida de cumplir la
métrica, pero escondía una limitación real. Las reclasifiqué como "dato faltante de un producto
existente" y se miden con su propia métrica.
- **Filtrar fragmentos por un porcentaje del mejor puntaje** para reducir ruido en el modo extractivo. Lo
propuso la IA, con un ejemplo concreto; las mediciones mostraron que hacía perder secciones correctas,
así que preferí mostrar un fragmento relacionado de más.
- **Considerar duplicados los textos "casi idénticos".** Lo descarté porque podía fusionar las
condiciones de dos créditos distintos; solo se deduplica el contenido idéntico tras normalizar.

**Proceso y seguridad**

- **Corregir los defectos de Gemini "aquí mismo"** durante la verificación, sin pasar por el ciclo de
tareas. Exigí abrirlos como tareas con prueba roja primero y revisión, justo en el componente de IA.
- **Forzar pillow 13** sobre el límite que declara `fastembed` para cerrar sus vulnerabilidades. Quedaba
fuera de la combinación soportada; acepté el riesgo documentado, porque no es alcanzable.
- **Commitear directamente en `main`** para rehacer un worktree, una de las opciones que ofreció un
agente. `main` está protegida en la constitución; todo llegó a `main` por PR.
- **Varios PRs apilados por especificación,** que el plan de entrega propuso por tamaño. El tamaño era
sobre todo `package-lock.json`; entregué un PR por característica, más fácil de revisar.
- **Ampliar el alcance con el LLM:** un proveedor configurable y un mensaje de ayuda redactado por el
modelo. Llegaron a estar en curso; los detuve y quedaron como mejoras futuras, porque el enunciado no
los pide.

## Cómo validé las respuestas de IA

- **TDD con evidencia:** ninguna implementación avanzó sin una prueba que fallara primero, registrada
por Mandao. Si una prueba pasaba a la primera, se exigía una mutación o una revisión independiente.
- **Revisión independiente:** un revisor con otro modelo aprobó o rechazó cada tarea. Hubo varios
rechazos que eran defectos reales. Por ejemplo, se podía responder sin registrar la consulta, y el
servidor de desarrollo exponía `Data/Información restringida.md`.
- **Evaluaciones de calidad** con el modelo real y un dataset de preguntas con respuesta esperada
(recuperación, "sin información" correcto, bloqueos y falsos positivos), con objetivos que bloquean el
CI si no se cumplen.
- **Llamadas reales a Gemini** antes de dar por bueno el diseño. Encontraron tres defectos que los dobles
de prueba ocultaban: un timeout que la API rechaza, montos de productos distintos mezclados y una
latencia mayor que el objetivo.
- **Pruebas manuales** y **CI** en cada PR.

---

## Decisiones técnicas para paso a productivo

### ¿Qué modelo utilizaría y por qué?

**Gemini 3.5 Flash-Lite**, en el nivel pago, para redactar a partir de los fragmentos recuperados:

- **El tamaño justo:** redactar a partir de uno a tres fragmentos cortos no necesita un modelo de
frontera. Google lo describe como el más rápido y económico de su familia.
- **Costo predecible:** USD 0,30 por millón de tokens de entrada y USD 2,50 por millón de salida (precios
de la documentación oficial, octubre de 2026).
- **Datos:** en el nivel pago, el contenido no se usa para mejorar los productos de Google; en el
gratuito, sí. Por eso el nivel gratuito solo se usó con los datos irreales de la prueba.
- **Sin dependencia del proveedor:** el modelo está detrás del puerto `Redactor`, así que cambiar de
proveedor no toca el caso de uso.

Para los embeddings mantendría inicialmente `paraphrase-multilingual-MiniLM-L12-v2`, que permite
ejecutar la búsqueda localmente. Evaluaría alternativas locales o de un proveedor según calidad de
recuperación en español, latencia, costo y privacidad, usando el mismo dataset antes de sustituirlo.


### ¿Cómo optimizaría costos?

- No llamar al modelo cuando la búsqueda no supera el umbral: esas preguntas cuestan cero.
- Usar el modo extractivo cuando basta, por ejemplo cuando la respuesta es un dato literal de una tabla.
- Cachear respuestas de preguntas repetidas, invalidando la caché cuando cambian los documentos (cada
fragmento ya tiene su hash).
- Enviar al modelo solo los fragmentos necesarios y limitar los tokens de salida.
- Medir el costo por consulta y por estado para ver dónde se gasta.

### ¿Cómo mitigaría Prompt Injection?

En capas, con las decisiones en código y no en el modelo:

1. **Guardrail de entrada determinista,** antes de buscar: bloquea los intentos de cambiar las
 instrucciones ("ignora tus instrucciones", "revela tu prompt"…) sobre el texto normalizado.
2. **Los documentos son datos, nunca instrucciones.** El documento confidencial, que incluso trae una
 instrucción maliciosa embebida, no se indexa.
3. **El prompt** le indica al modelo que use solo los fragmentos como fuente y que ignore las
 instrucciones que contengan.
4. **Guardrail de salida:** la respuesta solo puede citar fragmentos recuperados, y cada cifra debe estar
 en ellos. Si no, se usa la respuesta extractiva.
5. **En producción,** un clasificador dedicado como capa adicional, porque las reglas por patrones no
 reconocen pedidos disfrazados.

### ¿Qué guardrails implementaría?

Los que ya tiene la solución:

- validación de entrada (vacía, longitud, tipo de contenido, tamaño del cuerpo);
- bloqueo por seguridad en tres categorías (información restringida, prompt injection, datos de otros
clientes), con un mensaje genérico que no revela la regla;
- exclusión de documentos confidenciales del índice, por lista y por la marca CONFIDENCIAL;
- umbral de relevancia antes de responder;
- guardrail de salida sobre citas y cifras;
- logs sin el texto de las preguntas ni secretos;
- errores sin detalles internos.

Agregaría autenticación y autorización por rol, límite de tasa por usuario y detección de datos
personales en las preguntas antes de enviarlas a un proveedor externo.

### ¿Cómo monitorearía calidad?

- **Las evaluaciones del CI,** corridas también sobre una muestra de consultas reales anonimizadas.
- **La distribución de estados** (`Exitosa`, `Sin información suficiente`, `Bloqueada por seguridad`) y
sus cambios bruscos: muchas "sin información" indican documentos faltantes o umbrales mal calibrados.
- **La tasa de respaldo extractivo:** respuestas de Gemini rechazadas por el guardrail, timeouts y 429.
- **La opinión del asesor** sobre cada respuesta (útil o no útil) y una revisión humana periódica de una
muestra.

### ¿Cómo evolucionaría la solución hacia RAG?

Hoy la solución recupera fragmentos y responde con ellos de forma extractiva. La evolución es convertir
esa recuperación en el contexto de un LLM que redacte la respuesta, sin perder las fuentes ni el
mensaje fijo cuando no hay información. La base quedó preparada para ese cambio: el modelo vive detrás del puerto `Redactor`, ya
existe una implementación con Gemini que se activa con una clave, y el guardrail de salida y el respaldo
extractivo están probados. Aun así, el camino sería este:

- **Generación como modo principal.** El LLM recibe solo los fragmentos recuperados, cita los que usó y
dice qué parte de la pregunta no tiene soporte. El proveedor se elige por configuración detrás de
`Redactor`, y el modo extractivo queda como respaldo ante fallas o límites de cuota.
- **Mejor recuperación.** Un reranker sobre los candidatos de la búsqueda híbrida y una fragmentación
ajustada a cada tipo de documento, con solapamiento cuando una sección sea larga.
- **Ingesta continua.** Documentos versionados, reindexado incremental y la fecha de vigencia de cada
fuente, para no responder con una política vencida.
- **Evaluación continua.** El dataset de preguntas crece con casos reales anonimizados y mide fidelidad
a las fuentes, cobertura de citas y si dice que no tiene información cuando corresponde, con umbrales
que bloquean un cambio de modelo, prompt o fragmentación si empeoran.
- **Los mismos controles.** El guardrail de entrada sigue antes de buscar, y el de salida sigue
validando que cada cifra y cada cita salgan de un fragmento recuperado.

## Uso de Agentes

### ¿Utilizó agentes de desarrollo?

Sí. Claude Code con Mandao, que reparte el trabajo en roles:

- un **líder** que orquesta cada tarea;
- un **tester** que escribe las pruebas en rojo;
- un **implementer** que escribe el código;
- un **reviewer** independiente, con otro modelo, que aprueba o rechaza.

Trabajé además con varias sesiones en paralelo (backend, frontend e infraestructura), cada una en su rama.

### ¿Cómo fueron instruidos?

Con artefactos versionados, no con prompts sueltos:

- la **constitución** (principios, arquitectura, estándares, seguridad, glosario);
- la **especificación** de cada característica (historia con criterios GIVEN/WHEN/THEN, requisitos,
diseño y tareas con sus pruebas declaradas);
- un `AGENTS.md` por módulo con sus contratos y convenciones;
- un brief acotado por tarea.

Las decisiones que tomé quedaron escritas en esos documentos, así que cada agente partía de ellas.

### ¿Qué tareas delegó?

Redactar specs y tareas, escribir pruebas y código, revisar, investigar dependencias, configurar el CI y
los borradores de la documentación.

### ¿Qué tareas supervisó manualmente?

- Cada aprobación: constitución, historia, especificación y tareas.
- Las preguntas abiertas y los conflictos entre fuentes.
- Los riesgos aceptados.
- Las pruebas manuales en el navegador.
- Los PRs y los merges.

Cuando el resultado no convencía, lo corregí en la spec y no directamente en el código.

### ¿Qué decisiones no permitió tomar a la IA?

- El alcance y las prioridades.
- El stack y los cambios de arquitectura.
- Qué consultas se bloquean.
- Aceptar licencias y vulnerabilidades.
- Los textos que ve el usuario.
- Publicar, hacer push y mergear.

## Frontera entre IA y Desarrollo Tradicional

### ¿Qué responsabilidades resolvería mediante desarrollo tradicional?

Todo lo que decide:

- validar la entrada y bloquear por seguridad;
- decidir si hay soporte documental (búsqueda y umbral);
- aceptar o rechazar la salida del modelo;
- registrar las consultas y controlar errores;
- autenticar y autorizar.

Es código determinista, probado y auditable: la misma entrada da siempre el mismo resultado.

### ¿Qué responsabilidades delegaría a IA?

- Redactar la respuesta en lenguaje natural a partir de fragmentos ya recuperados.
- Representar el significado del texto (los embeddings).
- Más adelante, clasificar la intención de la pregunta como señal adicional, nunca como única decisión.

### ¿Qué responsabilidades nunca permitiría ejecutar a una IA?

- Decidir si se expone información restringida o de un cliente.
- Autorizar el acceso a datos.
- Escribir o modificar registros, o tomar decisiones con efecto financiero, como aprobar un crédito.
- Responder sin fuente verificable.

### ¿Cómo mantendría separadas estas responsabilidades?

Con la arquitectura:

- **El modelo solo existe detrás del puerto `Redactor`.** Recibe fragmentos ya filtrados y devuelve
texto, que pasa por un guardrail de salida en código.
- **Las decisiones viven en el dominio,** sin dependencias del modelo.
- **Cada regla tiene su prueba** y su evaluación en el CI.

## Optimización y Operación

Con 100.000 consultas diarias (≈ 1,2 por segundo en promedio, con picos varias veces mayores):

### ¿Qué componente tendría mayor riesgo de latencia?

La **llamada a Gemini**: 1 a 1,8 s por llamada en las pruebas reales, sujeta a los límites de cuota del
proveedor. Después, la **búsqueda vectorial en un solo proceso**, porque Qdrant en modo local no permite
varios workers.

### ¿Qué estrategia utilizaría para reducir tiempos de respuesta?

- No llamar al modelo bajo el umbral, y responder en modo extractivo cuando basta.
- Caché de respuestas y de vectores de preguntas frecuentes.
- Límite de concurrencia hacia el modelo (ya existe), timeout corto con respaldo extractivo (ya existe) y
streaming de la respuesta.
- Escalar horizontalmente: varios workers con Qdrant en modo servidor.

### ¿Qué podría cachear?

- Los vectores de los documentos: ya persisten y solo se recalculan si cambia un fragmento.
- Los vectores y las respuestas completas de preguntas repetidas, normalizadas e invalidadas cuando
cambia la base documental.
- Las decisiones de bloqueo, que son deterministas, para preguntas idénticas.

### ¿Qué monitorearía?

- Latencia p50 y p95 por etapa: validación, búsqueda, modelo y registro.
- Distribución de estados y de categorías de bloqueo.
- Tasa de 429, timeouts y respaldo extractivo.
- Errores 5xx con su `requestId`.
- Costo por consulta.
- Las métricas de evaluación sobre una muestra.

### ¿Cómo optimizaría costos de operación?

Lo mismo que en costos del modelo (no llamar bajo el umbral, caché, extractivo cuando basta, un modelo
pequeño y menos tokens), más una estimación para dimensionar: con unos 2.000 tokens de entrada y 200 de
salida por consulta, Gemini 3.5 Flash-Lite costaría ≈ USD 0,0011 por consulta, ≈ USD 110 al día si todas
llamaran al modelo. En la práctica sería menos, porque las preguntas sin soporte y las bloqueadas no lo
llaman.

## Persistencia y Gestión de Datos

### Qué mecanismo de almacenamiento seleccioné

- **SQLite:** registro de consultas (pregunta, fecha y hora en UTC, respuesta, fuentes y estado) y
búsqueda por palabras con FTS5.
- **Qdrant en modo local:** los vectores de los fragmentos.

### Por qué lo seleccioné

El enunciado pide una solución que corra completamente en local. SQLite viene con Python, no requiere
servidor ni configuración, y trae FTS5 para la búsqueda por palabras. Qdrant en modo local corre dentro
del proceso de Python, sin servidor, y no depende de que el Python cargue extensiones de SQLite (la causa
por la que descarté `sqlite-vec`).

### Qué ventajas tiene para este escenario

- Cero instalación: cualquier evaluador lo ejecuta con `uv sync`.
- Transacciones ACID: la consulta se registra completa o no se registra.
- Un solo archivo, fácil de inspeccionar y borrar.
- El mismo cliente de Qdrant sirve en producción contra un servidor.

## Escenario de Producción

### ¿Mantendría la misma solución de persistencia?

1. SQLite admite un solo escritor a la vez y Qdrant en modo local bloquea su carpeta, así que no escalan
a varios procesos o instancias.

### ¿Qué motor de base de datos utilizaría?

**PostgreSQL** gestionado para el registro de consultas, y **Qdrant en modo servidor** para los vectores
(o pgvector dentro del mismo PostgreSQL, si el volumen de documentos es moderado).

### ¿Por qué?

- PostgreSQL soporta escrituras concurrentes desde varias instancias, respaldos y réplicas, auditoría,
seguridad a nivel de fila y retención de datos, necesarios para un registro con información de
clientes.
- Qdrant en modo servidor escala la búsqueda vectorial y usa el mismo cliente que ya tiene la solución.
- pgvector simplifica la operación con un solo motor cuando el volumen lo permite.