"""T2 (MDO-0001): el contenido duplicado se indexa una sola vez (D6, C-2).

API asumida (src/server/infraestructura/documentos/cargador.py): la misma de T1,

    cargar_documentos(directorio: Path, excluidos: Sequence[str]) -> list[Fragmento]

que además descarta el contenido repetido: el hash es el sha256 del texto normalizado (minúsculas,
espacios colapsados), por documento y por fragmento; gana el primero en orden alfabético de archivo.
"""

from src.server.infraestructura.documentos.cargador import cargar_documentos

CONTENIDO = "# Guía\n\n## Uno\n\nTexto uno.\n\n## Dos\n\nTexto dos.\n"


def test_s21_dos_archivos_con_el_mismo_contenido_normalizado_indexan_solo_el_primero(tmp_path):
    (tmp_path / "A.md").write_text(CONTENIDO, encoding="utf-8")
    (tmp_path / "B.md").write_text(
        "# GUÍA\n\n## UNO\n\n  texto   UNO.\n\n## Dos\n\nTexto\n  dos.\n", encoding="utf-8"
    )

    fragmentos = cargar_documentos(tmp_path, [])

    assert [(f.documento, f.seccion) for f in fragmentos] == [("A", "Uno"), ("A", "Dos")]


def test_s21_gana_el_primero_en_orden_alfabetico_aunque_se_cree_despues(tmp_path):
    (tmp_path / "Z.md").write_text(CONTENIDO, encoding="utf-8")
    (tmp_path / "A.md").write_text(CONTENIDO, encoding="utf-8")

    fragmentos = cargar_documentos(tmp_path, [])

    assert {f.documento for f in fragmentos} == {"A"}


def test_s21_c1_ninguna_fuente_repite_el_mismo_contenido(tmp_path):
    (tmp_path / "A.md").write_text(CONTENIDO, encoding="utf-8")
    (tmp_path / "B.md").write_text(CONTENIDO.upper(), encoding="utf-8")

    fragmentos = cargar_documentos(tmp_path, [])

    textos = [" ".join(f.texto.casefold().split()) for f in fragmentos]
    assert len(textos) == len(set(textos))


def test_s21_una_seccion_repetida_en_dos_documentos_se_indexa_una_sola_vez(tmp_path):
    (tmp_path / "A.md").write_text(
        "# A\n\n## Comun\n\nMismo texto.\n\n## Propia A\n\nSolo en A.\n", encoding="utf-8"
    )
    (tmp_path / "B.md").write_text(
        "# B\n\n## Comun\n\n  mismo   TEXTO.\n\n## Propia B\n\nSolo en B.\n", encoding="utf-8"
    )

    fragmentos = cargar_documentos(tmp_path, [])

    assert [(f.documento, f.seccion) for f in fragmentos] == [
        ("A", "Comun"),
        ("A", "Propia A"),
        ("B", "Propia B"),
    ]


def test_s21_secciones_parecidas_pero_distintas_se_conservan_ambas(tmp_path):
    (tmp_path / "Credito A.md").write_text(
        "# Crédito A\n\n## Condiciones\n\nTasa 12% anual, plazo 24 meses.\n", encoding="utf-8"
    )
    (tmp_path / "Credito B.md").write_text(
        "# Crédito B\n\n## Condiciones\n\nTasa 18% anual, plazo 36 meses.\n", encoding="utf-8"
    )

    fragmentos = cargar_documentos(tmp_path, [])

    assert [(f.documento, f.seccion) for f in fragmentos] == [
        ("Credito A", "Condiciones"),
        ("Credito B", "Condiciones"),
    ]
