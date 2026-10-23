from http import HTTPStatus

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.responses import JSONResponse

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
    # Solo `loc` y `msg`: los errores de Pydantic incluyen la entrada (la pregunta, PII).
    partes = [
        f"{'.'.join(str(p) for p in e['loc'] if p != 'body') or 'cuerpo'}: {e['msg']}"
        for e in exc.errors()
    ]
    return problema(422, "La petición no es válida. " + "; ".join(partes), _request_id(request))


async def manejar_http(request: Request, exc: Exception) -> JSONResponse:
    if not isinstance(exc, StarletteHTTPException):
        raise exc
    detalle = DETALLES.get(exc.status_code, HTTPStatus(exc.status_code).phrase)
    return problema(exc.status_code, detalle, _request_id(request))
