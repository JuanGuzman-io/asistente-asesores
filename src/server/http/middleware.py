import time
import uuid

from starlette.types import ASGIApp, Message, Receive, Scope, Send

from src.server.http.logs import registrar_peticion
from src.server.http.problemas import DETALLES, problema

RUTA_CONSULTAR = "/api/consultar"
LIMITE_BYTES = 16 * 1024


class MiddlewareSolicitud:
    """ASGI (D8): `requestId`, 415, 413, 500 sin detalles y una línea de log JSON por petición."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        inicio = time.perf_counter()
        request_id = str(uuid.uuid4())
        estado = scope.setdefault("state", {})
        estado["request_id"] = request_id
        codigo = 0
        fallo: str | None = None

        async def enviar(mensaje: Message) -> None:
            nonlocal codigo
            if mensaje["type"] == "http.response.start":
                codigo = mensaje["status"]
                mensaje["headers"] = [
                    *mensaje.get("headers", []),
                    (b"x-request-id", request_id.encode()),
                ]
            await send(mensaje)

        try:
            await self._atender(scope, receive, enviar, request_id)
        except Exception as error:
            fallo = type(error).__name__
            if codigo == 0:  # si la respuesta ya empezó no se puede reemplazar
                codigo = 500
                respuesta = problema(500, DETALLES[500], request_id)
                await respuesta(scope, receive, enviar)
        registrar_peticion(
            request_id=request_id,
            codigo=codigo,
            inicio=inicio,
            fuentes=int(estado.get("fuentes", 0)),
            estado=estado.get("estado"),
            error=fallo,
            categoria=estado.get("categoria"),
        )

    async def _atender(self, scope: Scope, receive: Receive, send: Send, request_id: str) -> None:
        if scope["method"] != "POST" or scope["path"] != RUTA_CONSULTAR:
            await self.app(scope, receive, send)
            return
        cabeceras = {k.lower(): v for k, v in scope["headers"]}
        tipo = cabeceras.get(b"content-type", b"").decode("latin-1").split(";")[0].strip().lower()
        if tipo != "application/json":
            await problema(415, DETALLES[415], request_id)(scope, receive, send)
            return
        cuerpo = await _leer_cuerpo(receive, cabeceras.get(b"content-length"))
        if cuerpo is None:
            await problema(413, DETALLES[413], request_id)(scope, receive, send)
            return

        entregado = False

        async def repetir() -> Message:
            nonlocal entregado
            if entregado:
                return await receive()  # desconexión del cliente
            entregado = True
            return {"type": "http.request", "body": cuerpo, "more_body": False}

        await self.app(scope, repetir, send)


async def _leer_cuerpo(receive: Receive, content_length: bytes | None) -> bytes | None:
    """El cuerpo completo, o None si supera el límite (por cabecera o contando bytes)."""
    if content_length is not None:
        try:
            if int(content_length) > LIMITE_BYTES:
                return None
        except ValueError:
            return None
    partes: list[bytes] = []
    total = 0
    while True:
        mensaje = await receive()
        if mensaje["type"] != "http.request":
            return b"".join(partes)  # el cliente se fue
        trozo = mensaje.get("body", b"")
        total += len(trozo)
        if total > LIMITE_BYTES:
            return None
        partes.append(trozo)
        if not mensaje.get("more_body", False):
            return b"".join(partes)
