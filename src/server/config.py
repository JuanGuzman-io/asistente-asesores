from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
DIRECTORIO_DATOS = RAIZ / "Data"
DOCUMENTOS_EXCLUIDOS = ["Información restringida.md"]
# Almacenes locales del servidor (fuera de git): carpeta de Qdrant y SQLite de consultas e índice.
DIRECTORIO_ALMACEN = RAIZ / "almacen"
DIRECTORIO_QDRANT = DIRECTORIO_ALMACEN / "qdrant"
RUTA_SQLITE = DIRECTORIO_ALMACEN / "consultas.db"
MODELO_EMBEDDINGS = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
UMBRAL_ALTO = 0.60
UMBRAL_BAJO = 0.525
