"""T8 (MDO-0001): cada consulta procesada queda registrada completa (AC-14, D10, S-11.1, S-11.2).

API asumida (design.md nombra el puerto `RepositorioConsultas` y la tabla `consultas`, pero no fija
nombres ni firmas):

    src/server/infraestructura/persistencia/esquema.py
        crear_esquema(conexion: sqlite3.Connection) -> None
            CREATE TABLE IF NOT EXISTS consultas (columnas y CHECK de data-model.md), indice sobre
            fecha_hora y PRAGMA user_version = 1. Idempotente.
    src/server/infraestructura/persistencia/repositorio.py
        RepositorioConsultasSqlite(conexion: sqlite3.Connection)
            .registrar(*, request_id: str, pregunta: str, resultado: Resultado, modo: str) -> None
            Genera `fecha_hora` (UTC ISO 8601 con offset +00:00) y guarda `estado` como el NOMBRE
            del enum (`EXITOSA`, `SIN_INFORMACION`, `BLOQUEADA`) y `fuentes` como JSON
            `[{documento, seccion, fragmento}]`. INSERT en una transaccion propia: si falla, hace
            rollback, deja la conexion sin transaccion abierta y propaga el error original.
    src/server/aplicacion/consultar.py
        consultar(pregunta, *, buscador, redactor, repositorio=None, request_id=None) -> Resultado
            `repositorio` es opcional para no romper las pruebas de T5/T6; si se da, el resultado se
            registra ANTES de devolverlo y un fallo del repositorio se propaga (sin respuesta).
            `request_id` por defecto es un UUID v4 generado por el caso de uso.
            `modo`: `ninguno` cuando no se redacta (sin informacion); si hay redaccion es el
            atributo `modo` del redactor (`extractivo` o `modelo`).

Las peticiones rechazadas por validacion (413, 415, 422) nunca llegan al caso de uso (D10); su
prueba HTTP vive en T9. Aqui solo se prueba que sin llamar a `consultar` no hay filas.
"""

import json
import logging
import sqlite3
import uuid
from collections.abc import Iterator, Sequence
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from src.server.aplicacion.consultar import consultar
from src.server.dominio.estados import Estado
from src.server.dominio.modelos import Fragmento, Fuente, Resultado
from src.server.dominio.puertos import RespuestaRedactada, ResultadoBusqueda
from src.server.infraestructura.persistencia.esquema import crear_esquema
from src.server.infraestructura.persistencia.repositorio import RepositorioConsultasSqlite

IMPULSO = Fragmento(
    "Productos de Crédito", "Crédito Productivo Impulso", "Monto de 1 a 20 millones."
)
PREGUNTA_PII = "¿Qué crédito le sirve a Juan Pérez, cédula 1234567890?"


@pytest.fixture
def conexion(tmp_path: Path) -> Iterator[sqlite3.Connection]:
    con = sqlite3.connect(tmp_path / "consultas.db")
    crear_esquema(con)
    yield con
    con.close()


@pytest.fixture
def repositorio(conexion: sqlite3.Connection) -> RepositorioConsultasSqlite:
    return RepositorioConsultasSqlite(conexion)


def _filas(conexion: sqlite3.Connection) -> list[sqlite3.Row]:
    conexion.row_factory = sqlite3.Row
    return conexion.execute("SELECT * FROM consultas ORDER BY id").fetchall()


def _exitosa() -> Resultado:
    return Resultado(
        "Impulso financia de 1 a 20 millones.",
        [Fuente("Productos de Crédito", "Crédito Productivo Impulso", "Monto de 1 a 20 millones.")],
        Estado.EXITOSA,
    )


def _sin_info() -> Resultado:
    return Resultado("No tengo información suficiente para responder.", [], Estado.SIN_INFORMACION)


class BuscadorDoble:
    def __init__(self, fragmentos: Sequence[Fragmento], hay_soporte: bool) -> None:
        self._r = ResultadoBusqueda(fragmentos=fragmentos, hay_soporte=hay_soporte)

    def buscar(self, pregunta: str) -> ResultadoBusqueda:
        return self._r


class RedactorDoble:
    modo = "extractivo"

    def redactar(self, pregunta: str, fragmentos: Sequence[Fragmento]) -> RespuestaRedactada:
        return RespuestaRedactada("Impulso financia de 1 a 20 millones.", [1])


# --- esquema (data-model.md) ---------------------------------------------------------------


def test_esquema_crea_consultas_con_las_columnas_del_modelo_de_datos(conexion):
    columnas = {f[1]: f for f in conexion.execute("PRAGMA table_info(consultas)")}

    assert set(columnas) == {
        "id",
        "request_id",
        "pregunta",
        "fecha_hora",
        "respuesta",
        "fuentes",
        "estado",
        "modo",
    }
    for nombre in (
        "request_id",
        "pregunta",
        "fecha_hora",
        "respuesta",
        "fuentes",
        "estado",
        "modo",
    ):
        assert columnas[nombre][3] == 1, f"{nombre} debe ser NOT NULL"


def test_esquema_fija_user_version_1_indice_por_fecha_y_es_idempotente(conexion):
    crear_esquema(conexion)

    assert conexion.execute("PRAGMA user_version").fetchone()[0] == 1
    indices = [
        conexion.execute(f"PRAGMA index_info({i[1]})").fetchall()
        for i in conexion.execute("PRAGMA index_list(consultas)")
    ]
    assert any([c[2] for c in cols] == ["fecha_hora"] for cols in indices)


# --- S-11.1: los cinco campos -----------------------------------------------------------------


def test_s111_exitosa_queda_con_los_cinco_campos_y_el_modo(repositorio, conexion):
    antes = datetime.now(UTC) - timedelta(seconds=1)

    repositorio.registrar(
        request_id=str(uuid.uuid4()),
        pregunta="¿Cuánto financia Impulso?",
        resultado=_exitosa(),
        modo="extractivo",
    )

    (fila,) = _filas(conexion)
    assert fila["pregunta"] == "¿Cuánto financia Impulso?"
    assert fila["respuesta"] == "Impulso financia de 1 a 20 millones."
    assert fila["estado"] == "EXITOSA"
    assert fila["modo"] == "extractivo"
    assert json.loads(fila["fuentes"]) == [
        {
            "documento": "Productos de Crédito",
            "seccion": "Crédito Productivo Impulso",
            "fragmento": "Monto de 1 a 20 millones.",
        }
    ]
    fecha = datetime.fromisoformat(fila["fecha_hora"])
    assert fecha.utcoffset() == timedelta(0)
    assert antes <= fecha <= datetime.now(UTC) + timedelta(seconds=1)


def test_s111_sin_informacion_queda_con_fuentes_lista_vacia(repositorio, conexion):
    repositorio.registrar(
        request_id=str(uuid.uuid4()),
        pregunta="¿Va a llover mañana?",
        resultado=_sin_info(),
        modo="ninguno",
    )

    (fila,) = _filas(conexion)
    assert fila["estado"] == "SIN_INFORMACION"
    assert fila["modo"] == "ninguno"
    assert fila["fuentes"] == "[]"
    assert fila["respuesta"] == "No tengo información suficiente para responder."


def test_s111_la_fuente_con_tildes_se_guarda_sin_perder_texto(repositorio, conexion):
    r = Resultado("ok", [Fuente("Crédito", "Sección ñ", "Plazo ≤ 36 meses")], Estado.EXITOSA)

    repositorio.registrar(request_id=str(uuid.uuid4()), pregunta="p", resultado=r, modo="modelo")

    (fila,) = _filas(conexion)
    assert json.loads(fila["fuentes"]) == [
        {"documento": "Crédito", "seccion": "Sección ñ", "fragmento": "Plazo ≤ 36 meses"}
    ]


def test_s111_cada_consulta_tiene_su_propio_registro(repositorio, conexion):
    repositorio.registrar(
        request_id=str(uuid.uuid4()), pregunta="a", resultado=_exitosa(), modo="extractivo"
    )
    repositorio.registrar(
        request_id=str(uuid.uuid4()), pregunta="b", resultado=_sin_info(), modo="ninguno"
    )

    filas = _filas(conexion)
    assert [f["pregunta"] for f in filas] == ["a", "b"]
    assert [f["estado"] for f in filas] == ["EXITOSA", "SIN_INFORMACION"]
    assert filas[0]["request_id"] != filas[1]["request_id"]


def test_s111_las_fuentes_registradas_coinciden_con_las_devueltas_por_consultar(
    repositorio, conexion
):
    con_soporte = consultar(
        "¿Cuánto financia Impulso?",
        buscador=BuscadorDoble([IMPULSO], True),
        redactor=RedactorDoble(),
        repositorio=repositorio,
    )
    sin_soporte = consultar(
        "¿Va a llover?",
        buscador=BuscadorDoble([], False),
        redactor=RedactorDoble(),
        repositorio=repositorio,
    )

    exitosa, sin_info = _filas(conexion)
    assert exitosa["estado"] == "EXITOSA" and exitosa["modo"] == "extractivo"
    assert exitosa["respuesta"] == con_soporte.respuesta
    assert json.loads(exitosa["fuentes"]) == [
        {"documento": f.documento, "seccion": f.seccion, "fragmento": f.fragmento}
        for f in con_soporte.fuentes
    ]
    assert sin_info["estado"] == "SIN_INFORMACION" and sin_info["modo"] == "ninguno"
    assert sin_info["respuesta"] == sin_soporte.respuesta
    assert json.loads(sin_info["fuentes"]) == []
    assert exitosa["pregunta"] == "¿Cuánto financia Impulso?"
    assert sin_info["pregunta"] == "¿Va a llover?"
    uuid.UUID(exitosa["request_id"], version=4)


def test_s111_c1_sin_llamar_a_consultar_no_hay_registros(conexion):
    # Las peticiones rechazadas con 413/415/422 no llegan al caso de uso (D10); la prueba HTTP es T9.
    assert _filas(conexion) == []


# --- CHECK de estado y modo ---------------------------------------------------------------------


@pytest.mark.parametrize("estado", [Estado.EXITOSA, Estado.SIN_INFORMACION, Estado.BLOQUEADA])
def test_estado_acepta_los_tres_valores_incluida_bloqueada(repositorio, conexion, estado):
    r = Resultado("r", [], estado)

    repositorio.registrar(request_id=str(uuid.uuid4()), pregunta="p", resultado=r, modo="ninguno")

    assert [f["estado"] for f in _filas(conexion)] == [estado.name]


@pytest.mark.parametrize("modo", ["modelo", "extractivo", "ninguno"])
def test_modo_acepta_los_tres_valores(repositorio, conexion, modo):
    repositorio.registrar(
        request_id=str(uuid.uuid4()), pregunta="p", resultado=_exitosa(), modo=modo
    )

    assert [f["modo"] for f in _filas(conexion)] == [modo]


def test_modo_invalido_se_rechaza_y_no_deja_fila(repositorio, conexion):
    with pytest.raises(sqlite3.Error):
        repositorio.registrar(
            request_id=str(uuid.uuid4()), pregunta="p", resultado=_exitosa(), modo="gemini"
        )

    assert _filas(conexion) == []


def test_check_de_la_tabla_rechaza_estado_y_modo_fuera_de_los_valores(conexion):
    sql = (
        "INSERT INTO consultas(request_id, pregunta, fecha_hora, respuesta, fuentes, estado, modo)"
        " VALUES (?, 'p', '2026-01-01T00:00:00+00:00', 'r', '[]', ?, ?)"
    )
    with pytest.raises(sqlite3.IntegrityError):
        conexion.execute(sql, (str(uuid.uuid4()), "Exitosa", "ninguno"))
    with pytest.raises(sqlite3.IntegrityError):
        conexion.execute(sql, (str(uuid.uuid4()), "EXITOSA", "otro"))
    assert _filas(conexion) == []


def test_request_id_es_unico(repositorio, conexion):
    rid = str(uuid.uuid4())
    repositorio.registrar(request_id=rid, pregunta="a", resultado=_exitosa(), modo="extractivo")

    with pytest.raises(sqlite3.IntegrityError):
        repositorio.registrar(request_id=rid, pregunta="b", resultado=_sin_info(), modo="ninguno")

    assert [f["pregunta"] for f in _filas(conexion)] == ["a"]


# --- S-11.2: falla al guardar --------------------------------------------------------------------


def _contar_desde_otra_conexion(tmp_path: Path) -> int:
    otra = sqlite3.connect(tmp_path / "consultas.db")
    try:
        return int(otra.execute("SELECT COUNT(*) FROM consultas").fetchone()[0])
    finally:
        otra.close()


def test_falla_insert_consulta_no_deja_fila(tmp_path, repositorio, conexion):
    conexion.execute(
        "CREATE TRIGGER falla_antes BEFORE INSERT ON consultas "
        "BEGIN SELECT RAISE(ABORT, 'disco lleno'); END"
    )
    conexion.commit()

    with pytest.raises(sqlite3.Error, match="disco lleno"):
        repositorio.registrar(
            request_id=str(uuid.uuid4()), pregunta="p", resultado=_exitosa(), modo="extractivo"
        )

    assert conexion.in_transaction is False
    assert _contar_desde_otra_conexion(tmp_path) == 0


def test_falla_despues_del_insert_hace_rollback_y_no_deja_fila_incompleta(
    tmp_path, repositorio, conexion
):
    conexion.execute("CREATE TABLE auditoria (x TEXT NOT NULL)")
    conexion.execute(
        "CREATE TRIGGER falla_despues AFTER INSERT ON consultas "
        "BEGIN INSERT INTO auditoria(x) VALUES (NULL); END"
    )
    conexion.commit()

    with pytest.raises(sqlite3.Error):
        repositorio.registrar(
            request_id=str(uuid.uuid4()), pregunta="p", resultado=_exitosa(), modo="extractivo"
        )

    assert conexion.in_transaction is False
    assert _contar_desde_otra_conexion(tmp_path) == 0


def test_tras_una_falla_el_repositorio_sigue_registrando(repositorio, conexion):
    with pytest.raises(sqlite3.Error):
        repositorio.registrar(
            request_id=str(uuid.uuid4()), pregunta="p", resultado=_exitosa(), modo="invalido"
        )

    repositorio.registrar(
        request_id=str(uuid.uuid4()), pregunta="q", resultado=_sin_info(), modo="ninguno"
    )

    assert [f["pregunta"] for f in _filas(conexion)] == ["q"]


def test_s112_si_el_almacenamiento_falla_consultar_propaga_el_error(repositorio, conexion):
    conexion.execute("DROP TABLE consultas")
    conexion.commit()

    with pytest.raises(sqlite3.Error):
        consultar(
            "¿Cuánto financia Impulso?",
            buscador=BuscadorDoble([IMPULSO], True),
            redactor=RedactorDoble(),
            repositorio=repositorio,
        )


# --- PII (NFR-4): la pregunta solo vive en la base local ------------------------------------------


def test_pii_registrar_no_escribe_la_pregunta_en_los_logs(repositorio, caplog):
    with caplog.at_level(logging.DEBUG):
        repositorio.registrar(
            request_id=str(uuid.uuid4()),
            pregunta=PREGUNTA_PII,
            resultado=_exitosa(),
            modo="extractivo",
        )
        consultar(
            PREGUNTA_PII,
            buscador=BuscadorDoble([IMPULSO], True),
            redactor=RedactorDoble(),
            repositorio=repositorio,
        )

    assert "Juan Pérez" not in caplog.text
    assert "1234567890" not in caplog.text


def test_pii_la_pregunta_se_guarda_tal_cual_en_la_base_local(repositorio, conexion):
    repositorio.registrar(
        request_id=str(uuid.uuid4()), pregunta=PREGUNTA_PII, resultado=_sin_info(), modo="ninguno"
    )

    assert [f["pregunta"] for f in _filas(conexion)] == [PREGUNTA_PII]


def test_pii_el_texto_se_enlaza_como_parametro_no_se_interpola_en_el_sql(repositorio, conexion):
    maliciosa = "x'); DROP TABLE consultas; --"

    repositorio.registrar(
        request_id=str(uuid.uuid4()), pregunta=maliciosa, resultado=_sin_info(), modo="ninguno"
    )

    assert [f["pregunta"] for f in _filas(conexion)] == [maliciosa]
