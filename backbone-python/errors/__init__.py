"""
Catálogo de códigos de error backbone — alineado con backbone-go.

Formato: LL_NNNNNNN  (9 dígitos)

    LL      = prefijo de capa (11-14)
    NNNNNNN = secuencia de 7 dígitos empezando en 0000001

Tabla de capas:

    11 = Domain         → reglas de negocio, entidades, value objects
    12 = Application    → casos de uso, commands, queries
    13 = Interface      → handlers HTTP, adaptadores gRPC, CLI
    14 = Infrastructure → bases de datos, mensajería, caché, externos

Ejemplo:
    110000001  →  Domain, error #1
    120000001  →  Application, error #1
    130000001  →  Interface, error #1
    140000001  →  Infrastructure, error #1

Uso:
    from backbone.errors import ErrorCodes
    raise SomeException(code=ErrorCodes.DOMAIN_INVALID_VALUE, ...)

    # En el error builder:
    ErrorResponseBuilder.validation_error("msg", error_code=ErrorCodes.IFC_INVALID_REQUEST_BODY)
"""


class ErrorCodes:
    """Catálogo de códigos de error por capa arquitectural."""

    # ── Domain (11) ──────────────────────────────────────────────────────────
    DOMAIN_BUSINESS_RULE_VIOLATION  = 110000001
    DOMAIN_INVALID_ENTITY_STATE     = 110000002
    DOMAIN_INVALID_VALUE_OBJECT     = 110000003
    DOMAIN_AGGREGATE_INCONSISTENCY  = 110000004
    DOMAIN_INVALID_FILTER           = 110000005

    # ── Application (12) ─────────────────────────────────────────────────────
    APP_USE_CASE_FAILURE            = 120000001
    APP_VALIDATION_FAILURE          = 120000002
    APP_AUTHORIZATION_DENIED        = 120000003
    APP_RESOURCE_NOT_FOUND          = 120000004
    APP_EXTERNAL_SERVICE_FAILURE    = 120000005
    APP_CONFLICT                    = 120000006

    # ── Interface / HTTP (13) ────────────────────────────────────────────────
    IFC_INVALID_REQUEST_BODY        = 130000001
    IFC_METHOD_NOT_ALLOWED          = 130000002
    IFC_ROUTE_NOT_FOUND             = 130000003
    IFC_MISSING_REQUIRED_PARAM      = 130000004
    IFC_INVALID_FILTER_FORMAT       = 130000005
    IFC_UNAUTHORIZED                = 130000006
    IFC_FORBIDDEN                   = 130000007

    # ── Infrastructure (14) ──────────────────────────────────────────────────
    INFRA_DB_FAILURE                = 140000001
    INFRA_MESSAGING_FAILURE         = 140000002
    INFRA_CACHE_FAILURE             = 140000003
    INFRA_EXTERNAL_API_FAILURE      = 140000004
    INFRA_SERVICE_UNAVAILABLE       = 140000005

    @staticmethod
    def layer(code: int) -> int:
        """Extrae el prefijo de capa (2 dígitos) de un código de 9 dígitos."""
        return code // 10_000_000

    @staticmethod
    def number(code: int) -> int:
        """Extrae el número de secuencia (7 dígitos) de un código de 9 dígitos."""
        return code % 10_000_000

    @staticmethod
    def layer_name(code: int) -> str:
        """Nombre legible de la capa para logs."""
        names = {
            11: "domain",
            12: "application",
            13: "interface",
            14: "infrastructure",
        }
        return names.get(ErrorCodes.layer(code), "unknown")

    @staticmethod
    def is_valid(code: int) -> bool:
        """Valida que el código tenga formato correcto LL_NNNNNNN."""
        layer = ErrorCodes.layer(code)
        number = ErrorCodes.number(code)
        return 11 <= layer <= 19 and number >= 1
