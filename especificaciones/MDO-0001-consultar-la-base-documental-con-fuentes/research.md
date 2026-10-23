---
schema_version: 1
entries:
  - id: R1
    topic: "fastembed 0.9.0 multilingual models and Python support"
    topic_type: library
    question: "¿Qué modelo multilingüe de fastembed 0.9.0 usar para español y qué versión de Python lo soporta?"
    status: resolved
    decision: "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2 (384 dimensiones, 0,22 GB, apache-2.0) sobre Python 3.13."
    rationale: "Es el multilingüe más liviano de fastembed; las secciones de Data/ caben en su límite de 128 tokens. fastembed declara Python 3.10–3.15, pero su dependencia onnxruntime 1.31.0 no publica wheels cp315, así que se usa 3.13."
    alternatives: ["paraphrase-multilingual-mpnet-base-v2 (768, 1,00 GB, 512 tokens)", "intfloat/multilingual-e5-large (1024, 2,24 GB, prefijos query/passage)"]
    premise_ids: [P3]
    checked_on: "2026-10-23"
    expires: "2027-04-23"
    claims:
      - id: C1
        key: "fastembed version"
        kind: version
        value: "0.9.0"
        sources:
          - { tier: official, url: "https://pypi.org/pypi/fastembed/json", checked_on: "2026-10-23", value: "0.9.0" }
      - id: C2
        key: "onnxruntime macOS arm64 wheels"
        kind: version
        value: "cp311–cp314"
        sources:
          - { tier: official, url: "https://pypi.org/pypi/onnxruntime/1.31.0/json", checked_on: "2026-10-23", value: "cp311–cp314" }
      - id: C3
        key: "multilingual MiniLM model"
        kind: api
        value: "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2, 384 dim, 0,22 GB"
        sources:
          - { tier: manufacturer, url: "https://github.com/qdrant/fastembed/blob/main/fastembed/text/pooled_embedding.py", checked_on: "2026-10-23", value: "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2, 384 dim, 0,22 GB" }
          - { tier: manufacturer, url: "https://qdrant.github.io/fastembed/examples/Supported_Models/", checked_on: "2026-10-23", value: "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2, 384 dim, 0,22 GB" }
    contradictions: []
  - id: R2
    topic: "sqlite-vec 0.1.9 loading and vec0 KNN"
    topic_type: library
    question: "¿Cómo se carga sqlite-vec 0.1.9 en Python y qué exige del intérprete?"
    status: resolved
    decision: "No se usa sqlite-vec: se reemplaza por Qdrant local (requirements.md C-3, R5)."
    rationale: "sqlite-vec exige un sqlite3 de Python con extensiones cargables (enable_load_extension); el 3.13.4 de pyenv no lo permite (corrida del 2026-10-23) y la solución debe correr en local en cualquier máquina."
    alternatives: ["sqlite-vec 0.1.9 con un Python que permita extensiones (Homebrew)", "pysqlite3"]
    premise_ids: []
    checked_on: "2026-10-23"
    expires: "2027-04-23"
    claims:
      - id: C1
        key: "sqlite-vec version"
        kind: version
        value: "0.1.9"
        sources:
          - { tier: official, url: "https://pypi.org/pypi/sqlite-vec/0.1.9/json", checked_on: "2026-10-23", value: "0.1.9" }
      - id: C2
        key: "sqlite-vec loading"
        kind: api
        value: "conn.enable_load_extension(True); sqlite_vec.load(conn)"
        sources:
          - { tier: manufacturer, url: "https://alexgarcia.xyz/sqlite-vec/python.html", checked_on: "2026-10-23", value: "conn.enable_load_extension(True); sqlite_vec.load(conn)" }
    contradictions: []
  - id: R3
    topic: "SQLite FTS5 Spanish tokenization and safe MATCH"
    topic_type: api
    question: "¿FTS5 pliega tildes en español y cómo se pasa texto del usuario a MATCH sin errores de sintaxis?"
    status: resolved
    decision: "tokenize='unicode61 remove_diacritics 2'; cada palabra entre comillas dobles con comillas internas duplicadas, unidas con OR, siempre como parámetro; sin palabras, no se consulta FTS."
    rationale: "remove_diacritics 2 pliega todas las tildes latinas (además verificado en local, design.md P2); el texto entre comillas es una cadena literal, sin operadores. No hay stemming en español: la búsqueda semántica cubre las variantes."
    alternatives: ["porter (solo inglés)", "trigram (índice mayor, más ruido)"]
    premise_ids: [P2]
    checked_on: "2026-10-23"
    expires: "2027-04-23"
    claims:
      - id: C1
        key: "fts5 diacritics"
        kind: api
        value: "unicode61 remove_diacritics 2"
        sources:
          - { tier: official, url: "https://www.sqlite.org/fts5.html", checked_on: "2026-10-23", value: "unicode61 remove_diacritics 2" }
      - id: C2
        key: "fts5 string quoting"
        kind: api
        value: "cadena entre comillas dobles; una comilla interna se escribe duplicada"
        sources:
          - { tier: official, url: "https://www.sqlite.org/fts5.html", checked_on: "2026-10-23", value: "cadena entre comillas dobles; una comilla interna se escribe duplicada" }
    contradictions: []
  - id: R4
    topic: "FastAPI 0.161.1 content type, body limit, problem details; google-genai 2.33.0 timeout and schema"
    topic_type: api
    question: "¿Qué da FastAPI por defecto para Content-Type no JSON, límite de cuerpo y RFC 9457, y cómo se fija tiempo límite y salida estructurada en google-genai?"
    status: resolved
    decision: "Middleware ASGI propio para 415 y 413 (16 KB, contando bytes recibidos); handlers propios para RFC 9457; Gemini con HttpOptions(timeout=5000) sin retry_options, system_instruction separado y response_schema Pydantic."
    rationale: "FastAPI con strict_content_type=True (por defecto desde 0.132.0) responde 422, no 415, a un tipo no JSON; no tiene límite de cuerpo ni problem+json. google-genai no reintenta si no se fija retry_options (los ejemplos de Vertex con attempts=5 muestran el valor por defecto al fijarlo) y el timeout va en milisegundos."
    alternatives: ["RequestBodyLimitMiddleware de Starlette 1.6+ (responde 413 en texto plano y no está confirmado junto a FastAPI 0.161.1)", "strict_content_type=False"]
    premise_ids: []
    checked_on: "2026-10-23"
    expires: "2027-04-23"
    claims:
      - id: C1
        key: "fastapi version"
        kind: version
        value: "0.161.1"
        sources:
          - { tier: official, url: "https://pypi.org/project/fastapi/#history", checked_on: "2026-10-23", value: "0.161.1" }
      - id: C2
        key: "fastapi non-json content type"
        kind: api
        value: "422 (RequestValidationError); 415 requiere código propio"
        sources:
          - { tier: manufacturer, url: "https://raw.githubusercontent.com/fastapi/fastapi/0.161.1/fastapi/routing.py", checked_on: "2026-10-23", value: "422 (RequestValidationError); 415 requiere código propio" }
      - id: C3
        key: "fastapi error format"
        kind: api
        value: "{detail} application/json; sin RFC 9457"
        sources:
          - { tier: manufacturer, url: "https://raw.githubusercontent.com/fastapi/fastapi/0.161.1/fastapi/exception_handlers.py", checked_on: "2026-10-23", value: "{detail} application/json; sin RFC 9457" }
      - id: C4
        key: "google-genai version"
        kind: version
        value: "2.33.0"
        sources:
          - { tier: official, url: "https://pypi.org/project/google-genai/#history", checked_on: "2026-10-23", value: "2.33.0" }
      - id: C5
        key: "google-genai timeout and retries"
        kind: api
        value: "HttpOptions(timeout=<ms>); sin retry_options, un intento"
        sources:
          - { tier: manufacturer, url: "https://raw.githubusercontent.com/googleapis/python-genai/v2.33.0/google/genai/_api_client.py", checked_on: "2026-10-23", value: "HttpOptions(timeout=<ms>); sin retry_options, un intento" }
      - id: C6
        key: "gemini model code"
        kind: api
        value: "gemini-3.5-flash-lite (Stable)"
        sources:
          - { tier: official, url: "https://ai.google.dev/gemini-api/docs/models", checked_on: "2026-10-23", value: "gemini-3.5-flash-lite (Stable)" }
    contradictions: []
  - id: R5
    topic: "qdrant-client 1.20.0 local mode"
    topic_type: library
    question: "¿qdrant-client 1.20.0 corre sin servidor en modo local con persistencia, sobre Python 3.13 y con fastembed 0.9.0?"
    status: resolved
    decision: "Qdrant local con QdrantClient(path=…), qdrant-client 1.20.0; un solo cliente por proceso (design.md D13)."
    rationale: "El README documenta el modo local con persistencia en disco; PyPI declara Python >=3.10 y el extra fastembed >=0.9,<0.10. Verificado en local el 2026-10-23 con Python 3.13.16 y 3.13.4 (constitucion/CHANGELOG.md) y el bloqueo de carpeta en P6."
    alternatives: ["coseno en memoria (no es una base vectorial)", "Chroma", "LanceDB"]
    premise_ids: [P6]
    checked_on: "2026-10-23"
    expires: "2027-04-23"
    claims:
      - id: C1
        key: "qdrant-client version"
        kind: version
        value: "1.20.0"
        sources:
          - { tier: official, url: "https://pypi.org/pypi/qdrant-client/json", checked_on: "2026-10-23", value: "1.20.0" }
      - id: C2
        key: "qdrant local mode"
        kind: api
        value: "QdrantClient(path=\"path/to/db\") persiste en disco sin servidor"
        sources:
          - { tier: manufacturer, url: "https://raw.githubusercontent.com/qdrant/qdrant-client/master/README.md", checked_on: "2026-10-23", value: "QdrantClient(path=\"path/to/db\") persiste en disco sin servidor" }
    contradictions: []
---

# Research

Cinco preguntas que afectan decisiones del diseño, investigadas el 2026-10-23 con fuentes oficiales y del
fabricante. Decisiones en `design.md` (D1, D4, D5, D8, D9, D13).

- **R1:** modelo de embeddings y versión de Python → D1, D4.
- **R2:** `sqlite-vec` → descartado (C-3); queda como alternativa rechazada de D4.
- **R3:** FTS5 en español y consulta segura → D4, D5.
- **R4:** 413, 415 y RFC 9457 en FastAPI; tiempo límite y salida estructurada de Gemini → D8, D9.
- **R5:** Qdrant en modo local → D4, D11, D13.
