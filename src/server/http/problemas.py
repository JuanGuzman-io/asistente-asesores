from http import HTTPStatus

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.responses import JSONResponse

from src.server.http.esquemas import MENSAJES_PREGUNTA

DETALLE_CUERPO = "El cuerpo debe ser un JSON con el campo pregunta de tipo texto."
DETALLES = {
    404: "El recurso solicitado no existe.",
    405: "El método no está permitido para este recurso.",
    413: "El cuerpo supera el límite de 16.384 bytes.",
    415: "El Content-Type debe ser application/json.",
    500: "Ocurrió un error interno. Inténtalo de nuevo.",
}


def problema(codigo: int, detalle: str, request_id: str) -> JSONResponse:
    """Respuesta RFC 9457 (D8)."""
    return JSONResponse(
        {
            "type": "about:blank",
            "title": HTTPStatus(codigo).phrase,
            "status": codigo,
            "detail": detalle,
            "requestId": request_id,
        },
        status_code=codigo,
        media_type="application/problem+json",
    )


def _request_id(request: Request) -> str:
    return str(request.scope.get("state", {}).get("request_id", ""))


async def manejar_validacion(request: Request, exc: Exception) -> JSONResponse:
    if not isinstance(exc, RequestValidationError):
        raise exc
    # Texto fijo: los errores de Pydantic incluyen la entrada (la pregunta, PII) y no se copian.
    detalle = DETALLE_CUERPO
    for error in exc.errors():
        mensaje = str(error["msg"]).removeprefix("Value error, ")
        if error["type"] == "value_error" and mensaje in MENSAJES_PREGUNTA:
            detalle = mensaje
    return problema(422, detalle, _request_id(request))


async def manejar_http(request: Request, exc: Exception) -> JSONResponse:
    if not isinstance(exc, StarletteHTTPException):
        raise exc
    detalle = DETALLES.get(exc.status_code, HTTPStatus(exc.status_code).phrase)
    return problema(exc.status_code, detalle, _request_id(request))
