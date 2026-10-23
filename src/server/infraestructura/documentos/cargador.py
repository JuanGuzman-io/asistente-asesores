import hashlib
import logging
import unicodedata
from collections.abc import Sequence
from pathlib import Path

from src.server.dominio.modelos import Fragmento

registro = logging.getLogger(__name__)

LINEAS_ENCABEZADO = 10
MARCA_CONFIDENCIAL = "CONFIDENCIAL"


def _nfc(texto: str) -> str:
    return unicodedata.normalize("NFC", texto)


def _hash_normalizado(texto: str) -> str:
    normalizado = " ".join(texto.casefold().split())
    return hashlib.sha256(normalizado.encode("utf-8")).hexdigest()


def _es_confidencial(texto: str) -> bool:
    encabezado = texto.splitlines()[:LINEAS_ENCABEZADO]
    return any(MARCA_CONFIDENCIAL.casefold() in linea.casefold() for linea in encabezado)


def _fragmentar(documento: str, texto: str) -> list[Fragmento]:
    titulo = ""
    secciones: list[tuple[str, list[str]]] = []
    for linea in texto.splitlines():
        if linea.startswith("# ") and not titulo:
            titulo = linea[2:].strip()
        elif linea.startswith("## "):
            secciones.append((linea[3:].strip(), []))
        elif secciones:
            secciones[-1][1].append(linea)
    if not secciones:
        cuerpo = "\n".join(
            linea for linea in texto.splitlines() if not linea.startswith("# ")
        ).strip()
        secciones = [(titulo or documento, [cuerpo])]
    fragmentos = [Fragmento(documento, seccion, "\n".join(c).strip()) for seccion, c in secciones]
    return [f for f in fragmentos if f.texto]


def cargar_documentos(directorio: Path, excluidos: Sequence[str]) -> list[Fragmento]:
    omitidos = {_nfc(nombre) for nombre in excluidos}
    fragmentos: list[Fragmento] = []
    hashes_documento: set[str] = set()
    hashes_fragmento: set[str] = set()
    for ruta in sorted(directorio.glob("*.md")):
        nombre = _nfc(ruta.name)
        if nombre in omitidos:
            registro.info("Documento excluido por lista: %s", nombre)
            continue
        texto = ruta.read_text(encoding="utf-8")
        if _es_confidencial(texto):
            registro.info("Documento excluido por CONFIDENCIAL: %s", nombre)
            continue
        hash_documento = _hash_normalizado(texto)
        if hash_documento in hashes_documento:
            registro.info("Documento duplicado omitido: %s", nombre)
            continue
        hashes_documento.add(hash_documento)
        for fragmento in _fragmentar(nombre.removesuffix(".md"), texto):
            hash_fragmento = _hash_normalizado(fragmento.texto)
            if hash_fragmento not in hashes_fragmento:
                hashes_fragmento.add(hash_fragmento)
                fragmentos.append(fragmento)
    return fragmentos
