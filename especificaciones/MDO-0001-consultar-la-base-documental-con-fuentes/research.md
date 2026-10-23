---
schema_version: 1
entries:
  - id: R1
    topic: "fastembed 0.9.0 multilingual models and Python support"
    topic_type: library
    question: "¿Qué modelo multilingüe de fastembed 0.9.0 usar para español y qué versión de Python lo soporta?"
    status: resolved
    decision: "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2 (384 dimensiones, 0,22 GB, apache-2.0) sobre Python 3.13."
    rationale: "Es el multilingüe más liviano de fastembed; las secciones de Data/ caben en su límite de 128 tokens; onnxruntime 1.31.0 no publica wheels cp315, por lo que Python 3.15 no sirve."
    alternatives: ["paraphrase-multilingual-mpnet-base-v2 (768, 1,00 GB, 512 tokens)", "intfloat/multilingual-e5-large (1024, 2,24 GB, prefijos query/passage)"]
    premise_ids: [P3]
    checked_on: "2026-10-23"
    expires: "2027-01-21"
    claims:
      - id: C1
        key: "fastembed version"
        kind: version
        value: "0.9.0, subido 2026-10-07, requires_python >=3.10.0, declara 3.10–3.15"
        sources:
          - { tier: official, url: "https://pypi.org/pypi/fastembed/json", checked_on: "2026-10-23", value: "0.9.0" }
      - id: C2
        key: "onnxruntime wheels"
        kind: version
        value: "1.31.0 (2026-10-09): macOS arm64 solo cp311–cp314; sin cp315 en ninguna plataforma"
        sources:
          - { tier: official, url: "https://pypi.org/pypi/onnxruntime/1.31.0/json", checked_on: "2026-10-23", value: "cp311–cp314" }
      - id: C3
        key: "multilingual models"
        kind: api
        value: "paraphrase-multilingual-MiniLM-L12-v2 384/0,22 GB/128 tokens; paraphrase-multilingual-mpnet-base-v2 768/1,00 GB/512 tokens; multilingual-e5-large 1024/2,24 GB"
        sources:
          - { tier: manufacturer, url: "https://github.com/qdrant/fastembed/blob/main/fastembed/text/pooled_embedding.py", checked_on: "2026-10-23", value: "lista de modelos (rama main)" }
          - { tier: manufacturer, url: "https://qdrant.github.io/fastembed/examples/Supported_Models/", checked_on: "2026-10-23", value: "misma lista" }
    contradictions:
      - "fastembed declara Python 3.15, pero su dependencia onnxruntime no publica wheel cp315: se resuelve usando Python 3.13."
  - id: R2
    topic: "sqlite-vec 0.1.9 loading and vec0 KNN"
    topic_type: library
    question: "¿Cómo se carga sqlite-vec 0.1.9 en Python, en qué plataformas y cómo se consulta por vecinos con coseno?"
    status: resolved
    decision: "No se usa sqlite-vec (requirements.md C-3): coseno en memoria sobre embeddings en BLOB."
    rationale: "sqlite-vec exige un sqlite3 de Python con extensiones cargables; el 3.13.4 de pyenv no lo permite (corrida del 2026-10-23) y no todos los evaluadores lo tendrían. Con ~20 fragmentos, el coseno en memoria basta."
    alternatives: ["sqlite-vec 0.1.9 con un Python que permita extensiones (Homebrew)", "pysqlite3"]
    premise_ids: []
    checked_on: "2026-10-23"
    expires: "2027-01-21"
    claims:
      - id: C1
        key: "sqlite-vec version"
        kind: version
        value: "0.1.9, subido 2026-03-31, wheels macosx_11_0_arm64, manylinux2014, win_amd64"
        sources:
          - { tier: official, url: "https://pypi.org/pypi/sqlite-vec/0.1.9/json", checked_on: "2026-10-23", value: "0.1.9" }
      - id: C2
        key: "loading and knn"
        kind: api
        value: "enable_load_extension + sqlite_vec.load; vec0(... float[N] distance_metric=cosine); WHERE embedding MATCH :q AND k = N"
        sources:
          - { tier: manufacturer, url: "https://alexgarcia.xyz/sqlite-vec/python.html", checked_on: "2026-10-23", value: "load" }
          - { tier: manufacturer, url: "https://alexgarcia.xyz/sqlite-vec/features/knn.html", checked_on: "2026-10-23", value: "knn" }
    contradictions: []
  - id: R3
    topic: "SQLite FTS5 Spanish tokenization and safe MATCH"
    topic_type: api
    question: "¿FTS5 pliega tildes en español y cómo se pasa texto del usuario a MATCH sin errores de sintaxis?"
    status: resolved
    decision: "tokenize='unicode61 remove_diacritics 2'; cada palabra entre comillas dobles con comillas internas duplicadas, unidas con OR, siempre como parámetro; sin palabras, no se consulta FTS."
    rationale: "remove_diacritics 2 pliega todas las tildes latinas; el texto entre comillas es una cadena literal, sin operadores. No hay stemming en español: la búsqueda semántica cubre las variantes."
    alternatives: ["porter (solo inglés)", "trigram (índice mayor, más ruido)"]
    premise_ids: [P2]
    checked_on: "2026-10-23"
    expires: "2027-01-21"
    claims:
      - id: C1
        key: "fts5 tokenizer and quoting"
        kind: api
        value: "unicode61 remove_diacritics 2; cadenas entre comillas con \"\" para la comilla"
        sources:
          - { tier: official, url: "https://www.sqlite.org/fts5.html", checked_on: "2026-10-23", value: "tokenizer y sintaxis de consulta" }
    contradictions: []
  - id: R4
    topic: "FastAPI 0.161.1 content type, body limit, problem details; google-genai 2.33.0 timeout and schema"
    topic_type: api
    question: "¿Qué da FastAPI por defecto para Content-Type no JSON, límite de cuerpo y RFC 9457, y cómo se fija tiempo límite y salida estructurada en google-genai?"
    status: resolved
    decision: "Middleware ASGI propio para 415 y 413 (16 KB, contando bytes recibidos); handlers propios para RFC 9457; Gemini con HttpOptions(timeout=5000) sin retry_options, system_instruction separado y response_schema Pydantic."
    rationale: "FastAPI con strict_content_type=True (por defecto desde 0.132.0) responde 422, no 415, a un tipo no JSON; no tiene límite de cuerpo ni problem+json; google-genai no reintenta si no se fija retry_options y el timeout va en milisegundos."
    alternatives: ["RequestBodyLimitMiddleware de Starlette 1.6+ (responde 413 en texto plano y no está confirmado junto a FastAPI 0.161.1)", "strict_content_type=False"]
    premise_ids: []
    checked_on: "2026-10-23"
    expires: "2027-01-21"
    claims:
      - id: C1
        key: "fastapi version and content type"
        kind: api
        value: "0.161.1 (2026-10-22); solo application/json y application/*+json se parsean; otro tipo → 422"
        sources:
          - { tier: official, url: "https://pypi.org/project/fastapi/#history", checked_on: "2026-10-23", value: "0.161.1" }
          - { tier: official, url: "https://fastapi.tiangolo.com/advanced/strict-content-type/", checked_on: "2026-10-23", value: "strict_content_type" }
          - { tier: manufacturer, url: "https://raw.githubusercontent.com/fastapi/fastapi/0.161.1/fastapi/routing.py", checked_on: "2026-10-23", value: "422 por lectura del código" }
      - id: C2
        key: "body limit and problem details"
        kind: api
        value: "sin límite de cuerpo en FastAPI; Starlette 1.6.0 agrega max_body_size con 413 en texto plano; sin soporte RFC 9457"
        sources:
          - { tier: manufacturer, url: "https://raw.githubusercontent.com/Kludex/starlette/main/starlette/middleware/body_limit.py", checked_on: "2026-10-23", value: "413 texto plano" }
          - { tier: manufacturer, url: "https://raw.githubusercontent.com/fastapi/fastapi/0.161.1/fastapi/exception_handlers.py", checked_on: "2026-10-23", value: "{detail} application/json" }
      - id: C3
        key: "google-genai timeout, retries, schema, model"
        kind: api
        value: "2.33.0 (2026-10-23); HttpOptions(timeout=ms); sin retry_options un solo intento; GenerateContentConfig(system_instruction, response_mime_type='application/json', response_schema); gemini-3.5-flash-lite estable"
        sources:
          - { tier: official, url: "https://pypi.org/project/google-genai/#history", checked_on: "2026-10-23", value: "2.33.0" }
          - { tier: manufacturer, url: "https://raw.githubusercontent.com/googleapis/python-genai/v2.33.0/google/genai/_api_client.py", checked_on: "2026-10-23", value: "timeout y reintentos" }
          - { tier: manufacturer, url: "https://googleapis.github.io/python-genai/", checked_on: "2026-10-23", value: "salida estructurada" }
          - { tier: official, url: "https://ai.google.dev/gemini-api/docs/models", checked_on: "2026-10-23", value: "gemini-3.5-flash-lite Stable" }
    contradictions:
      - "Ejemplos de Vertex muestran attempts=5: es el valor por defecto al fijar retry_options, no el del cliente (sin reintentos)."
      - "google-genai 2.33.0 se publicó el 2026-10-23, el mismo día: se fija 2.33.0 pero conviene esperar o usar 2.32.0 si aparece un problema (riesgo R-5 en design.md)."
---

# Research

Cuatro preguntas que afectan decisiones del diseño, investigadas el 2026-10-23 con fuentes oficiales y del
fabricante. Decisiones en `design.md` (D4, D5, D8, D9).

- **R1:** modelo de embeddings y versión de Python → D4.
- **R2:** carga de `sqlite-vec` → descartado en C-3; queda como alternativa de D4.
- **R3:** FTS5 en español y consulta segura → D4, D5.
- **R4:** 413, 415 y RFC 9457 en FastAPI; tiempo límite y salida estructurada de Gemini → D8, D9.
