import sys
import tempfile
from importlib.metadata import version

from qdrant_client import QdrantClient

print("python", sys.version.split()[0], "qdrant-client", version("qdrant-client"))
with tempfile.TemporaryDirectory() as path:
    first = QdrantClient(path=path)
    try:
        second = QdrantClient(path=path)
        print("second client on same path: opened (no lock)")
        second.close()
    except Exception as exc:  # the probe reports whatever the client raises
        print("second client on same path: refused ->", type(exc).__name__, str(exc).splitlines()[0][:160])
    first.close()
