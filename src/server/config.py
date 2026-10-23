from pathlib import Path

DIRECTORIO_DATOS = Path(__file__).resolve().parents[2] / "Data"
DOCUMENTOS_EXCLUIDOS = ["Información restringida.md"]
MODELO_EMBEDDINGS = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
