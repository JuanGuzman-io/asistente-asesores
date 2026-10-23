"""T10 (MDO-0001) evals EV-1 a EV-5 en modo extractivo sobre `tests/fixtures/consultas.json@v1`.

Usan el modelo REAL de embeddings (`EmbeddingsFastembed`, ~0,22 GB la primera vez): un doble no sirve
para calibrar los umbrales `UMBRAL_ALTO` / `UMBRAL_BAJO` (D4, C-5, P5). Es la excepción documentada
a "las pruebas no descargan modelos" (standards.md), por eso llevan el marker `eval`.

Cada pregunta pasa por HTTP (`crear_app` real, `RedactorExtractivo`, umbrales de `config.py`). Además
de pasar o fallar, se imprimen los valores medidos de EV-1 a EV-5 y la distribución del mejor coseno
con y sin soporte (para calibrar). Ejecutar con `-s` o leer el resumen de la terminal.

Definiciones (requirements.md, "Eval thresholds"):
  EV-1 (AC-3)  hit@3: (documento, sección) esperado entre las fuentes, sobre con_respuesta + parcial >= 0,90
  EV-2 (AC-11) sin_respuesta + fuera_de_tema con estado `Sin información suficiente`           >= 0,90
  EV-3 (AC-3)  con_respuesta + parcial con estado `Sin información suficiente`                 <= 0,10
  EV-4 (AC-4)  respuestas `Exitosa` cuyas cifras están todas en los fragmentos citados          == 1,00
  EV-5 (AC-6)  respuestas `Exitosa` con >= 1 fuente completa (documento, sección, fragmento)    == 1,00
EV-6 (parciales con modelo) queda fuera: requiere Gemini y las pruebas nunca lo llaman.
"""

import json
import re
import statistics
import unicodedata
from dataclasses import dataclass
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from src.server.config import DIRECTORIO_DATOS, DOCUMENTOS_EXCLUIDOS, UMBRAL_ALTO, UMBRAL_BAJO
from src.server.http.app import crear_app
from src.server.infraestructura.busqueda.embeddings import EmbeddingsFastembed
from src.server.infraestructura.busqueda.indice import COLECCION
from src.server.infraestructura.redactor.extractivo import RedactorExtractivo

pytestmark = pytest.mark.eval

DATASET = Path(__file__).resolve().parents[2] / "fixtures" / "consultas.json"
CON_SOPORTE = {"con_respuesta", "parcial"}
SIN_SOPORTE = {"sin_respuesta", "fuera_de_tema"}
CIFRA = re.compile(r"\d+(?:[.,]\d+)*%?")
SIN_INFO = "Sin información suficiente"
PREGUNTA_PDF = "¿Cuál es el monto máximo del Crédito Productivo Impulso?"


def _nfc(texto: str) -> str:
    return unicodedata.normalize("NFC", texto)


@dataclass
class Medicion:
    consulta: dict
    estado: str
    fuentes: list[dict]
    respuesta: str
    coseno: float  # mejor coseno de la pregunta contra todo el índice (sin umbral)


@pytest.fixture(scope="module")
def mediciones(tmp_path_factory, request) -> list[Medicion]:
    dataset = json.loads(DATASET.read_text(encoding="utf-8"))
    assert dataset["version"] == "v1"
    base = tmp_path_factory.mktemp("evals")
    embeddings = EmbeddingsFastembed()
    app = crear_app(
        directorio_datos=DIRECTORIO_DATOS,
        excluidos=DOCUMENTOS_EXCLUIDOS,
        directorio_qdrant=base / "qdrant",
        ruta_sqlite=base / "consultas.db",
        embeddings=embeddings,
        redactor=RedactorExtractivo(),
    )
    resultado: list[Medicion] = []
    with TestClient(app) as cliente:
        for consulta in dataset["consultas"]:
            respuesta = cliente.post("/api/consultar", json={"pregunta": consulta["pregunta"]})
            assert respuesta.status_code == 200, consulta["id"]
            cuerpo = respuesta.json()
            vector = embeddings.embeber([consulta["pregunta"]])[0]
            mejor = app.state.qdrant.query_points(COLECCION, query=vector, limit=1).points[0].score
            resultado.append(
                Medicion(consulta, cuerpo["estado"], cuerpo["fuentes"], cuerpo["respuesta"], mejor)
            )
    _imprimir_reporte(request, resultado)
    return resultado


def _tasa(aciertos: int, total: int) -> float:
    assert total > 0, "el dataset no tiene preguntas para esta métrica"
    return aciertos / total


def _ev1(m: list[Medicion]) -> float:
    base = [x for x in m if x.consulta["tipo"] in CON_SOPORTE]
    esperado = lambda x: (x.consulta["documento"], x.consulta["seccion"])  # noqa: E731
    hits = [
        x for x in base if esperado(x) in {(_nfc(f["documento"]), f["seccion"]) for f in x.fuentes}
    ]
    return _tasa(len(hits), len(base))


def _ev2(m: list[Medicion]) -> float:
    base = [x for x in m if x.consulta["tipo"] in SIN_SOPORTE]
    return _tasa(sum(x.estado == SIN_INFO for x in base), len(base))


def _ev3(m: list[Medicion]) -> float:
    base = [x for x in m if x.consulta["tipo"] in CON_SOPORTE]
    return _tasa(sum(x.estado == SIN_INFO for x in base), len(base))


def _ev4(m: list[Medicion]) -> float:
    exitosas = [x for x in m if x.estado == "Exitosa"]
    fieles = [
        x
        for x in exitosas
        if set(CIFRA.findall(x.respuesta))
        <= set(CIFRA.findall(" ".join(f["fragmento"] for f in x.fuentes)))
    ]
    return _tasa(len(fieles), len(exitosas))


def _ev5(m: list[Medicion]) -> float:
    exitosas = [x for x in m if x.estado == "Exitosa"]
    completas = [
        x
        for x in exitosas
        if x.fuentes and all(f["documento"] and f["seccion"] and f["fragmento"] for f in x.fuentes)
    ]
    return _tasa(len(completas), len(exitosas))


def _resumen(valores: list[float]) -> str:
    if not valores:
        return "sin datos"
    return (
        f"n={len(valores)} min={min(valores):.3f} mediana={statistics.median(valores):.3f} "
        f"max={max(valores):.3f}"
    )


def _imprimir_reporte(request, m: list[Medicion]) -> None:
    salida = request.config.pluginmanager.getplugin("terminalreporter")
    escribir = salida.write_line if salida else print
    escribir("")
    escribir(f"=== EVALS consultas@v1 (umbrales alto={UMBRAL_ALTO} bajo={UMBRAL_BAJO}) ===")
    escribir(
        f"EV-1={_ev1(m):.3f} (>=0.90)  EV-2={_ev2(m):.3f} (>=0.90)  EV-3={_ev3(m):.3f} (<=0.10)  "
        f"EV-4={_ev4(m):.3f} (==1.00)  EV-5={_ev5(m):.3f} (==1.00)"
    )
    con = [x.coseno for x in m if x.consulta["tipo"] in CON_SOPORTE]
    sin = [x.coseno for x in m if x.consulta["tipo"] in SIN_SOPORTE]
    escribir(f"mejor coseno CON soporte: {_resumen(con)}")
    escribir(f"mejor coseno SIN soporte: {_resumen(sin)}")
    escribir("id   tipo           coseno estado                     hit  pregunta")
    for x in sorted(m, key=lambda x: x.coseno):
        c = x.consulta
        hit = "-"
        if c["documento"]:
            hit = "si" if any(f["seccion"] == c["seccion"] for f in x.fuentes) else "NO"
        escribir(
            f"{c['id']:<4} {c['tipo']:<14} {x.coseno:6.3f} {x.estado:<26} {hit:<4} {c['pregunta']}"
        )


def test_dataset_v1_cubre_los_cuatro_tipos_con_muestra_suficiente():
    consultas = json.loads(DATASET.read_text(encoding="utf-8"))["consultas"]
    tipos = {t: sum(c["tipo"] == t for c in consultas) for t in CON_SOPORTE | SIN_SOPORTE}
    assert all(n >= 3 for n in tipos.values()), tipos
    assert sum(tipos[t] for t in CON_SOPORTE) >= 20  # muestra de EV-1 y EV-3
    assert sum(tipos[t] for t in SIN_SOPORTE) >= 10  # muestra de EV-2


def test_s3_1_la_pregunta_del_pdf_trae_primero_el_credito_productivo_impulso(mediciones):
    medicion = next(x for x in mediciones if x.consulta["pregunta"] == PREGUNTA_PDF)

    assert medicion.estado == "Exitosa"
    primera = medicion.fuentes[0]
    assert (_nfc(primera["documento"]), primera["seccion"]) == (
        "Productos de Crédito",
        "Crédito Productivo Impulso",
    )


def test_ev1_recuperacion_hit_at_3(mediciones):
    assert _ev1(mediciones) >= 0.90


def test_ev2_precision_de_sin_informacion(mediciones):
    assert _ev2(mediciones) >= 0.90


def test_ev3_falsos_sin_informacion(mediciones):
    assert _ev3(mediciones) <= 0.10


def test_ev4_fidelidad_de_las_cifras(mediciones):
    assert _ev4(mediciones) == 1.00


def test_ev5_fuentes_completas(mediciones):
    assert _ev5(mediciones) == 1.00
