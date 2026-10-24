import re
import unicodedata

from src.server.dominio.estados import CategoriaBloqueo


def normalizar(texto: str) -> str:
    """D4: sin tildes, en minúsculas y con espacios colapsados; conserva la puntuación."""
    descompuesto = unicodedata.normalize("NFKD", texto)
    sin_marcas = "".join(c for c in descompuesto if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", sin_marcas.casefold()).strip()


def _compilar(*patrones: str) -> tuple[re.Pattern[str], ...]:
    return tuple(re.compile(p) for p in patrones)


def _v(n: int) -> str:
    """Ventana de 0 a n palabras con separadores no alfanuméricos (la puntuación no la rompe).

    `\\W+\\w+` no se solapa consigo mismo: sin ambigüedad, lineal (NFR-1).
    """
    return rf"(?:\W+\w+){{0,{n}}}\W+"


_ANULAR = r"\b(?:ignora|ignore|olvida|omite|descarta|salta|desobedece|anula|disregard|forget)\b"
_REGLAS = r"(?:reglas|indicaciones|restricciones|directrices|rules|guidelines|restrictions)"
_MOSTRAR = r"\b(?:muestra|muestrame|revela|repite|dime|imprime|escribe)\b"

PROMPT_INJECTION = _compilar(
    # (a) anular instrucciones; "reglas" solo con calificador ("omite las reglas de pago": no)
    _ANULAR + _v(4) + r"(?:instrucciones|prompt|lo anterior|instructions|previous)\b",
    _ANULAR + _v(3) + r"(?:tus|todas|your|all)" + _v(2) + _REGLAS + r"\b",
    _ANULAR + _v(3) + _REGLAS + r" (?:anteriores|previas|del sistema|originales)\b",
    # (b) cambio de rol
    r"\bahora,? (?:eres|seras|actua|responde)\b",
    r"(?:^|[.!?¿¡:;] ?)(?:actua|comportate) como\b",
    r"\bfinge (?:ser|que)\b",
    r"\bhaz de cuenta que\b",
    r"\bmodo (?:desarrollador|developer|administrador|dios|sin restricciones)\b",
    r"\bjailbreak\b",
    r"\b(?:eres|seas|seras|asistente|modo|responde|responder) sin "
    r"(?:restricciones|filtros|censura|limites)\b",
    # (c) pedir el prompt
    r"\b(?:prompt del sistema|system prompt)\b",
    # "las instrucciones para..." (un trámite) no es pedir el prompt
    _MOSTRAR
    + _v(3)
    + r"(?:(?:tus|sus) (?:instrucciones|reglas)|las reglas|las instrucciones(?!\W+para\b))\b",
    _MOSTRAR + _v(3) + r"prompt\b",
    # (d) delimitadores del prompt
    r"</?(?:pregunta|fragmento|system|sistema|instrucciones)\b",
    r"\[/?inst\]",
)

_CREDENCIAL = r"(?:clave|contrasena|password|token|credencial(?:es)?|usuario)"
_CALIFICADOR = (
    r"(?:internos?|internas?|temporal(?:es)?|del sistema|central|administrador|admin|root"
    r"|maestra|del servidor|de (?:la )?base de datos|de produccion|del asistente)"
)

_PROCEDIMIENTO = r"(?:cambiar|restablecer|recuperar|renovar|crear|generar|desbloquear)"
_VENTANA_SIN_PROCEDIMIENTO = rf"(?:\W+(?!{_PROCEDIMIENTO}\b)\w+){{0,4}}\W+"

INFORMACION_RESTRINGIDA = _compilar(
    # (a) nombra lo reservado
    r"\binformacion (?:restringida|confidencial|tecnologica reservada)\b",
    r"\bdocumentos? confidencial(?:es)?\b",
    r"\bconfiguraciones? internas?\b",
    r"\bvariables? de entorno\b",
    r"\bapi[ _]?key\b",
    r"\bclave de (?:la )?api\b",
    r"\bgemini_api_key\b",
    r"\.env\b",
    # (b) credencial con calificador interno
    r"\b" + _CREDENCIAL + r"\b" + _v(4) + _CALIFICADOR + r"\b",
    # "de acceso" no cuenta si la credencial es ajena ("su clave de acceso", "sus claves de acceso")
    r"(?<!\bsu )(?<!\bsus )\b" + _CREDENCIAL + r"\b" + _v(4) + r"de acceso\b",
    # (c) pedido directo de credencial
    r"\b(?:cual|cuales) (?:es|son) (?:(?:el|la|los|las|tu|tus|su|sus) )?"
    r"(?:clave|contrasena|password|token|credencial(?:es)?)\b",
    # sin cruzar palabras de procedimiento: "dime como cambiar la clave" es una pregunta legítima
    r"\b(?:dame|dime|muestrame|revela|comparte|pasame|enviame|proporciona)\b"
    + _VENTANA_SIN_PROCEDIMIENTO
    + _CREDENCIAL
    + r"\b",
)

_DATO = (
    r"\b(?:saldo|deuda|telefono|celular|direccion|correo|cedula|numero de cuenta|historial"
    r"|movimientos|datos personales|informacion personal)\b"
)
# 6+ dígitos identifican a un cliente en cualquier lugar, salvo un monto (`$`, pesos, cop, millones)
_IDENTIFICADOR = r"(?<!\$)(?<!\$ )\d{6,}\b(?! (?:pesos|cop|millones)\b)"
_IDENTIFICADO = (
    r"\b(?:(?:senor|senora|sr|sra|don|dona)\.?\W+[a-z]{3,}|cliente llamad[oa]|"
    + _IDENTIFICADOR
    + r")\b"
)
_PEDIDO = (
    r"\b(?:dame|dime|muestrame|pasame|consulta|busca|revisa|trae|lista|necesito|quiero"
    r"|(?:cual|cuales) (?:es|son)|cuanto (?:debe|tiene))\b"
)

DATOS_DE_CLIENTES = _compilar(
    # (a) datos de otro cliente con un verbo de pedido
    _PEDIDO + _v(6) + r"otr[oa]s? client(?:e|es|a|as)\b",
    # (b) dato personal junto a un cliente identificado
    _DATO + _v(6) + _IDENTIFICADO,
    _IDENTIFICADO + _v(6) + _DATO[2:],
)

# Orden de D2: gana la primera familia que aplica.
_FAMILIAS = (
    (CategoriaBloqueo.PROMPT_INJECTION, PROMPT_INJECTION),
    (CategoriaBloqueo.INFORMACION_RESTRINGIDA, INFORMACION_RESTRINGIDA),
    (CategoriaBloqueo.DATOS_DE_CLIENTES, DATOS_DE_CLIENTES),
)


def evaluar_entrada(pregunta: str) -> CategoriaBloqueo | None:
    texto = normalizar(pregunta)
    for categoria, patrones in _FAMILIAS:
        if any(p.search(texto) for p in patrones):
            return categoria
    return None
