"""T1 (MDO-0001): carga y fragmentación por sección, sin documentos confidenciales.

API asumida (src/server/infraestructura/documentos/cargador.py):

    cargar_documentos(directorio: Path, excluidos: Sequence[str]) -> list[Fragmento]

    Fragmento: objeto con atributos `documento` (nombre del archivo sin `.md`),
    `seccion` (título `##`, o el `#` si el documento no tiene `##`) y `texto`.

El log de arranque usa el módulo `logging` y registra el nombre del excluido, nunca su contenido.
"""

import logging
import unicodedata
from pathlib import Path

import pytest

from src.server.infraestructura.documentos.cargador import cargar_documentos

DATA = Path(__file__).resolve().parents[4] / "Data"
RESTRINGIDO = "Información restringida.md"
OFICIALES = {
    "Manual del Asesor Comercial",
    "Políticas de Atención",
    "Portafolio de Microseguros",
    "Procedimientos Operativos",
    "Productos de Crédito",
}


def _nfc(texto: str) -> str:
    return unicodedata.normalize("NFC", texto)


def test_s11_los_cinco_documentos_oficiales_se_fragmentan_con_documento_y_seccion():
    fragmentos = cargar_documentos(DATA, [RESTRINGIDO])

    documentos = {_nfc(f.documento) for f in fragmentos}
    assert documentos == OFICIALES
    assert "Políticas de Atención" in documentos
    for f in fragmentos:
        assert f.documento and f.seccion and f.texto.strip()


def test_s11_c1_ningun_fragmento_proviene_de_informacion_restringida():
    fragmentos = cargar_documentos(DATA, [RESTRINGIDO])

    assert all(_nfc(f.documento) != "Información restringida" for f in fragmentos)
    # Ninguna línea sustantiva del archivo restringido aparece en un fragmento
    # (se compara como lista vacía para no imprimir el contenido).
    lineas = [
        linea.strip()
        for linea in (DATA / RESTRINGIDO).read_text(encoding="utf-8").splitlines()
        if len(linea.strip()) > 25
    ]
    filtradas = [n for n, linea in enumerate(lineas) if any(linea in f.texto for f in fragmentos)]
    assert filtradas == []


def test_s11_cada_seccion_h2_es_un_fragmento_con_sus_subsecciones(tmp_path):
    (tmp_path / "Guia.md").write_text(
        "# Guía\n\nIntro.\n\n## Uno\n\nTexto uno.\n\n### Detalle\n\nMás uno.\n\n## Dos\n\nTexto dos.\n",
        encoding="utf-8",
    )

    fragmentos = cargar_documentos(tmp_path, [])

    assert [(f.documento, f.seccion) for f in fragmentos] == [("Guia", "Uno"), ("Guia", "Dos")]
    assert "Más uno." in fragmentos[0].texto
    assert "Texto dos." not in fragmentos[0].texto
    assert "Texto dos." in fragmentos[1].texto


def test_s11_documento_sin_h2_es_un_solo_fragmento_titulado_con_su_h1(tmp_path):
    (tmp_path / "Breve.md").write_text(
        "# Nota breve\n\nPrimer párrafo.\n\nSegundo párrafo.\n", encoding="utf-8"
    )

    fragmentos = cargar_documentos(tmp_path, [])

    assert len(fragmentos) == 1
    assert fragmentos[0].documento == "Breve"
    assert fragmentos[0].seccion == "Nota breve"
    assert "Primer párrafo." in fragmentos[0].texto
    assert "Segundo párrafo." in fragmentos[0].texto


def test_s11_c1_un_archivo_de_la_lista_de_excluidos_no_genera_fragmentos(tmp_path):
    (tmp_path / "Oficial.md").write_text("# Oficial\n\n## A\n\nvisible\n", encoding="utf-8")
    (tmp_path / "Secreto.md").write_text("# Secreto\n\n## B\n\nCLAVE-OCULTA-1\n", encoding="utf-8")

    fragmentos = cargar_documentos(tmp_path, ["Secreto.md"])

    assert {f.documento for f in fragmentos} == {"Oficial"}
    assert all("CLAVE-OCULTA-1" not in f.texto for f in fragmentos)


def test_s12_documento_confidencial_por_encabezado_se_excluye_aunque_no_este_en_la_lista(
    tmp_path, caplog
):
    (tmp_path / "Oficial.md").write_text("# Oficial\n\n## A\n\nvisible\n", encoding="utf-8")
    (tmp_path / "Nuevo reservado.md").write_text(
        "# Nuevo reservado\n\n> CONFIDENCIAL: solo gerencia\n\n## Montos\n\nSECRETO-XYZ-987\n",
        encoding="utf-8",
    )

    with caplog.at_level(logging.DEBUG):
        fragmentos = cargar_documentos(tmp_path, [])

    assert {f.documento for f in fragmentos} == {"Oficial"}
    assert all("SECRETO-XYZ-987" not in f.texto for f in fragmentos)


@pytest.mark.parametrize("marca", ["Confidencial", "confidencial"])
def test_s12_marca_confidencial_se_detecta_sin_importar_mayusculas(tmp_path, caplog, marca):
    (tmp_path / "Oficial.md").write_text("# Oficial\n\n## A\n\nvisible\n", encoding="utf-8")
    (tmp_path / "Nuevo reservado.md").write_text(
        f"# Nuevo reservado\n\n> {marca}: solo gerencia\n\n## Montos\n\nSECRETO-XYZ-987\n",
        encoding="utf-8",
    )

    with caplog.at_level(logging.DEBUG):
        fragmentos = cargar_documentos(tmp_path, [])

    assert {f.documento for f in fragmentos} == {"Oficial"}
    assert all("SECRETO-XYZ-987" not in f.texto for f in fragmentos)


def test_s12_el_log_nombra_el_excluido_y_no_contiene_su_contenido(tmp_path, caplog):
    (tmp_path / "Oficial.md").write_text("# Oficial\n\n## A\n\nvisible\n", encoding="utf-8")
    (tmp_path / "Nuevo reservado.md").write_text(
        "# Titulo interno\n\nCONFIDENCIAL\n\n## Montos\n\nSECRETO-XYZ-987\n", encoding="utf-8"
    )
    (tmp_path / "Lista.md").write_text("# Lista\n\n## Z\n\nCLAVE-OCULTA-2\n", encoding="utf-8")

    with caplog.at_level(logging.DEBUG):
        cargar_documentos(tmp_path, ["Lista.md"])

    registro = caplog.text
    assert "Nuevo reservado" in registro
    assert "Lista" in registro
    for contenido in ("SECRETO-XYZ-987", "CLAVE-OCULTA-2", "Montos", "Titulo interno"):
        assert contenido not in registro
