import pathlib
import re

for p in sorted(pathlib.Path("Data").glob("*.md")):
    if p.name == "Información restringida.md":
        continue
    parts = re.split(r"(?m)^## ", p.read_text(encoding="utf-8"))
    sizes = [len(s.encode()) for s in parts[1:]]
    print(p.name, "sections", len(sizes), "max_bytes", max(sizes) if sizes else None)
