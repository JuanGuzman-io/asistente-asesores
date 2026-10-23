import json
import logging
import time

logger = logging.getLogger("asistente.http")


def configurar_logs() -> None:
    """Deja el logger de peticiones en INFO con salida propia (idempotente)."""
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        logger.addHandler(logging.StreamHandler())


def registrar_peticion(
    *,
    request_id: str,
    codigo: int,
    inicio: float,
    fuentes: int,
    estado: str | None,
    error: str | None = None,
) -> None:
    """Una línea JSON por petición (NFR-4). Nunca lleva la pregunta ni el resultado."""
    linea: dict[str, object] = {
        "requestId": request_id,
        "codigo": codigo,
        "latenciaMs": round((time.perf_counter() - inicio) * 1000, 1),
        "fuentes": fuentes,
    }
    if estado is not None:
        linea["estado"] = estado
    if error is not None:
        # Solo el tipo de la excepción: su mensaje puede traer la pregunta o el resultado (PII).
        linea["error"] = error
    logger.info(json.dumps(linea, ensure_ascii=False))
