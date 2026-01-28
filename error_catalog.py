"""
Catálogo centralizado de errores del sistema.
Define todos los códigos de error con sus mensajes y HTTP status codes.
"""
from typing import Dict, Optional
from enum import Enum


class ErrorCode(str, Enum):
    """Códigos de error del sistema."""
    
    # Errores de Autenticación (401)
    INVALID_CREDENTIALS = "AUTH_001"
    TOKEN_EXPIRED = "AUTH_002"
    TOKEN_INVALID = "AUTH_003"
    TOKEN_MISSING = "AUTH_004"
    UNAUTHORIZED = "AUTH_005"
    
    # Errores de Autorización (403)
    FORBIDDEN = "AUTHZ_001"
    INSUFFICIENT_PERMISSIONS = "AUTHZ_002"
    ROLE_REQUIRED = "AUTHZ_003"
    
    # Errores de Validación (400)
    INVALID_INPUT = "VAL_001"
    MISSING_FIELD = "VAL_002"
    INVALID_EMAIL_FORMAT = "VAL_003"
    INVALID_PHONE_FORMAT = "VAL_004"
    INVALID_PASSWORD_FORMAT = "VAL_005"
    WEAK_PASSWORD = "VAL_006"
    INVALID_DATE_FORMAT = "VAL_007"
    INVALID_COORDINATES = "VAL_008"
    INVALID_RATING = "VAL_009"
    
    # Errores de Duplicación (409)
    EMAIL_ALREADY_EXISTS = "DUP_001"
    IDENTIFICATION_ALREADY_EXISTS = "DUP_002"
    LICENSE_ALREADY_EXISTS = "DUP_003"
    VEHICLE_PLATE_ALREADY_EXISTS = "DUP_004"
    RESOURCE_ALREADY_EXISTS = "DUP_005"
    
    # Errores de Recurso No Encontrado (404)
    USER_NOT_FOUND = "NF_001"
    DRIVER_NOT_FOUND = "NF_002"
    BOOKING_NOT_FOUND = "NF_003"
    TRIP_NOT_FOUND = "NF_004"
    ROUTE_NOT_FOUND = "NF_005"
    RESOURCE_NOT_FOUND = "NF_006"
    
    # Errores de Estado (412)
    USER_INACTIVE = "STATE_001"
    USER_DELETED = "STATE_002"
    DRIVER_NOT_VERIFIED = "STATE_003"
    DRIVER_NOT_AVAILABLE = "STATE_004"
    BOOKING_ALREADY_ASSIGNED = "STATE_005"
    BOOKING_ALREADY_CANCELLED = "STATE_006"
    TRIP_ALREADY_STARTED = "STATE_007"
    TRIP_ALREADY_COMPLETED = "STATE_008"
    INVALID_STATE_TRANSITION = "STATE_009"
    LICENSE_EXPIRED = "STATE_010"
    LICENSE_EXPIRING_SOON = "STATE_011"
    
    # Errores de Negocio (422)
    UNDERAGE_USER = "BUS_001"
    VEHICLE_TOO_OLD = "BUS_002"
    INVALID_VEHICLE_CAPACITY = "BUS_003"
    INVALID_VEHICLE_YEAR = "BUS_004"
    BOOKING_TOO_LATE = "BUS_005"
    BOOKING_TOO_EARLY = "BUS_006"
    MAX_PASSENGERS_EXCEEDED = "BUS_007"
    ROUTE_TOO_LONG = "BUS_008"
    COORDINATES_OUT_OF_BOUNDS = "BUS_009"
    NO_DRIVERS_AVAILABLE = "BUS_010"
    
    # Errores de Base de Datos (500)
    DATABASE_ERROR = "DB_001"
    DATABASE_CONNECTION_ERROR = "DB_002"
    DATABASE_CONSTRAINT_ERROR = "DB_003"
    DATABASE_INTEGRITY_ERROR = "DB_004"
    
    # Errores de Servidor (500)
    INTERNAL_SERVER_ERROR = "SRV_001"
    SERVICE_UNAVAILABLE = "SRV_002"
    EXTERNAL_SERVICE_ERROR = "SRV_003"
    CONFIGURATION_ERROR = "SRV_004"
    
    # Errores de Rate Limiting (429)
    RATE_LIMIT_EXCEEDED = "RL_001"
    TOO_MANY_REQUESTS = "RL_002"


class ErrorCatalog:
    """
    Catálogo de errores con información detallada.
    Cada error incluye: código, mensaje, HTTP status y descripción.
    """
    
    ERRORS: Dict[str, Dict[str, any]] = {
        # Errores de Autenticación (401)
        ErrorCode.INVALID_CREDENTIALS: {
            "message": "Email o contraseña incorrectos",
            "http_status": 401,
            "description": "Las credenciales proporcionadas no son válidas"
        },
        ErrorCode.TOKEN_EXPIRED: {
            "message": "El token ha expirado",
            "http_status": 401,
            "description": "El token JWT ha expirado, solicite uno nuevo"
        },
        ErrorCode.TOKEN_INVALID: {
            "message": "Token inválido",
            "http_status": 401,
            "description": "El token proporcionado no es válido"
        },
        ErrorCode.TOKEN_MISSING: {
            "message": "Token no proporcionado",
            "http_status": 401,
            "description": "Se requiere un token de autenticación"
        },
        ErrorCode.UNAUTHORIZED: {
            "message": "No autorizado",
            "http_status": 401,
            "description": "Se requiere autenticación para acceder a este recurso"
        },
        
        # Errores de Autorización (403)
        ErrorCode.FORBIDDEN: {
            "message": "Acceso prohibido",
            "http_status": 403,
            "description": "No tiene permisos para acceder a este recurso"
        },
        ErrorCode.INSUFFICIENT_PERMISSIONS: {
            "message": "Permisos insuficientes",
            "http_status": 403,
            "description": "No tiene los permisos necesarios para esta operación"
        },
        ErrorCode.ROLE_REQUIRED: {
            "message": "Rol requerido no cumplido",
            "http_status": 403,
            "description": "Se requiere un rol específico para esta operación"
        },
        
        # Errores de Validación (400)
        ErrorCode.INVALID_INPUT: {
            "message": "Datos de entrada inválidos",
            "http_status": 400,
            "description": "Los datos proporcionados no cumplen con el formato esperado"
        },
        ErrorCode.MISSING_FIELD: {
            "message": "Campo requerido faltante",
            "http_status": 400,
            "description": "Falta un campo requerido en la solicitud"
        },
        ErrorCode.INVALID_EMAIL_FORMAT: {
            "message": "Formato de email inválido",
            "http_status": 400,
            "description": "El email proporcionado no tiene un formato válido"
        },
        ErrorCode.INVALID_PHONE_FORMAT: {
            "message": "Formato de teléfono inválido",
            "http_status": 400,
            "description": "El número de teléfono debe ser ecuatoriano válido"
        },
        ErrorCode.INVALID_PASSWORD_FORMAT: {
            "message": "Formato de contraseña inválido",
            "http_status": 400,
            "description": "La contraseña no cumple con los requisitos mínimos"
        },
        ErrorCode.WEAK_PASSWORD: {
            "message": "Contraseña débil",
            "http_status": 400,
            "description": "La contraseña debe tener al menos 8 caracteres, mayúscula y número"
        },
        ErrorCode.INVALID_DATE_FORMAT: {
            "message": "Formato de fecha inválido",
            "http_status": 400,
            "description": "La fecha debe estar en formato ISO 8601"
        },
        ErrorCode.INVALID_COORDINATES: {
            "message": "Coordenadas inválidas",
            "http_status": 400,
            "description": "Las coordenadas geográficas no son válidas"
        },
        ErrorCode.INVALID_RATING: {
            "message": "Rating inválido",
            "http_status": 400,
            "description": "El rating debe estar entre 1.0 y 5.0"
        },
        
        # Errores de Duplicación (409)
        ErrorCode.EMAIL_ALREADY_EXISTS: {
            "message": "El email ya está registrado",
            "http_status": 409,
            "description": "Ya existe un usuario con este email"
        },
        ErrorCode.IDENTIFICATION_ALREADY_EXISTS: {
            "message": "El número de identificación ya está registrado",
            "http_status": 409,
            "description": "Ya existe un usuario con este número de identificación"
        },
        ErrorCode.LICENSE_ALREADY_EXISTS: {
            "message": "La licencia ya está registrada",
            "http_status": 409,
            "description": "Ya existe un conductor con este número de licencia"
        },
        ErrorCode.VEHICLE_PLATE_ALREADY_EXISTS: {
            "message": "La placa del vehículo ya está registrada",
            "http_status": 409,
            "description": "Ya existe un conductor con esta placa"
        },
        ErrorCode.RESOURCE_ALREADY_EXISTS: {
            "message": "El recurso ya existe",
            "http_status": 409,
            "description": "Ya existe un recurso con estos identificadores"
        },
        
        # Errores de Recurso No Encontrado (404)
        ErrorCode.USER_NOT_FOUND: {
            "message": "Usuario no encontrado",
            "http_status": 404,
            "description": "No existe un usuario con el ID proporcionado"
        },
        ErrorCode.DRIVER_NOT_FOUND: {
            "message": "Conductor no encontrado",
            "http_status": 404,
            "description": "No existe un conductor con el ID proporcionado"
        },
        ErrorCode.BOOKING_NOT_FOUND: {
            "message": "Reserva no encontrada",
            "http_status": 404,
            "description": "No existe una reserva con el ID proporcionado"
        },
        ErrorCode.TRIP_NOT_FOUND: {
            "message": "Viaje no encontrado",
            "http_status": 404,
            "description": "No existe un viaje con el ID proporcionado"
        },
        ErrorCode.ROUTE_NOT_FOUND: {
            "message": "Ruta no encontrada",
            "http_status": 404,
            "description": "No existe una ruta con el ID proporcionado"
        },
        ErrorCode.RESOURCE_NOT_FOUND: {
            "message": "Recurso no encontrado",
            "http_status": 404,
            "description": "El recurso solicitado no existe"
        },
        
        # Errores de Estado (412)
        ErrorCode.USER_INACTIVE: {
            "message": "Usuario inactivo",
            "http_status": 412,
            "description": "El usuario está inactivo, contacte al administrador"
        },
        ErrorCode.USER_DELETED: {
            "message": "Usuario eliminado",
            "http_status": 412,
            "description": "El usuario ha sido eliminado"
        },
        ErrorCode.DRIVER_NOT_VERIFIED: {
            "message": "Conductor no verificado",
            "http_status": 412,
            "description": "El conductor aún no ha sido verificado"
        },
        ErrorCode.DRIVER_NOT_AVAILABLE: {
            "message": "Conductor no disponible",
            "http_status": 412,
            "description": "El conductor no está disponible actualmente"
        },
        ErrorCode.BOOKING_ALREADY_ASSIGNED: {
            "message": "Reserva ya asignada",
            "http_status": 412,
            "description": "La reserva ya tiene un conductor asignado"
        },
        ErrorCode.BOOKING_ALREADY_CANCELLED: {
            "message": "Reserva ya cancelada",
            "http_status": 412,
            "description": "La reserva ya fue cancelada previamente"
        },
        ErrorCode.TRIP_ALREADY_STARTED: {
            "message": "Viaje ya iniciado",
            "http_status": 412,
            "description": "El viaje ya ha sido iniciado"
        },
        ErrorCode.TRIP_ALREADY_COMPLETED: {
            "message": "Viaje ya completado",
            "http_status": 412,
            "description": "El viaje ya ha sido completado"
        },
        ErrorCode.INVALID_STATE_TRANSITION: {
            "message": "Transición de estado inválida",
            "http_status": 412,
            "description": "La transición de estado solicitada no es válida"
        },
        ErrorCode.LICENSE_EXPIRED: {
            "message": "Licencia expirada",
            "http_status": 412,
            "description": "La licencia de conducir ha expirado"
        },
        ErrorCode.LICENSE_EXPIRING_SOON: {
            "message": "Licencia por expirar",
            "http_status": 412,
            "description": "La licencia expira en menos de 30 días"
        },
        
        # Errores de Negocio (422)
        ErrorCode.UNDERAGE_USER: {
            "message": "Usuario menor de edad",
            "http_status": 422,
            "description": "Debes tener al menos 18 años para registrarte"
        },
        ErrorCode.VEHICLE_TOO_OLD: {
            "message": "Vehículo demasiado antiguo",
            "http_status": 422,
            "description": "El vehículo debe ser del año 2010 o posterior"
        },
        ErrorCode.INVALID_VEHICLE_CAPACITY: {
            "message": "Capacidad del vehículo inválida",
            "http_status": 422,
            "description": "La capacidad debe estar entre 1 y 15 pasajeros"
        },
        ErrorCode.INVALID_VEHICLE_YEAR: {
            "message": "Año del vehículo inválido",
            "http_status": 422,
            "description": "El año del vehículo no es válido"
        },
        ErrorCode.BOOKING_TOO_LATE: {
            "message": "Reserva demasiado tarde",
            "http_status": 422,
            "description": "No se puede hacer reservas con menos de 2 horas de anticipación"
        },
        ErrorCode.BOOKING_TOO_EARLY: {
            "message": "Reserva demasiado temprana",
            "http_status": 422,
            "description": "No se puede hacer reservas con más de 30 días de anticipación"
        },
        ErrorCode.MAX_PASSENGERS_EXCEEDED: {
            "message": "Capacidad máxima excedida",
            "http_status": 422,
            "description": "El número de pasajeros excede la capacidad del vehículo"
        },
        ErrorCode.ROUTE_TOO_LONG: {
            "message": "Ruta demasiado larga",
            "http_status": 422,
            "description": "La ruta excede el tiempo máximo de viaje de 5 horas"
        },
        ErrorCode.COORDINATES_OUT_OF_BOUNDS: {
            "message": "Coordenadas fuera de Ecuador",
            "http_status": 422,
            "description": "Las coordenadas deben estar dentro del territorio ecuatoriano"
        },
        ErrorCode.NO_DRIVERS_AVAILABLE: {
            "message": "No hay conductores disponibles",
            "http_status": 422,
            "description": "No hay conductores disponibles en este momento"
        },
        
        # Errores de Base de Datos (500)
        ErrorCode.DATABASE_ERROR: {
            "message": "Error de base de datos",
            "http_status": 500,
            "description": "Ocurrió un error al acceder a la base de datos"
        },
        ErrorCode.DATABASE_CONNECTION_ERROR: {
            "message": "Error de conexión a base de datos",
            "http_status": 500,
            "description": "No se pudo conectar a la base de datos"
        },
        ErrorCode.DATABASE_CONSTRAINT_ERROR: {
            "message": "Error de restricción de base de datos",
            "http_status": 500,
            "description": "La operación viola una restricción de base de datos"
        },
        ErrorCode.DATABASE_INTEGRITY_ERROR: {
            "message": "Error de integridad de datos",
            "http_status": 500,
            "description": "La operación viola la integridad de los datos"
        },
        
        # Errores de Servidor (500)
        ErrorCode.INTERNAL_SERVER_ERROR: {
            "message": "Error interno del servidor",
            "http_status": 500,
            "description": "Ocurrió un error inesperado en el servidor"
        },
        ErrorCode.SERVICE_UNAVAILABLE: {
            "message": "Servicio no disponible",
            "http_status": 503,
            "description": "El servicio no está disponible temporalmente"
        },
        ErrorCode.EXTERNAL_SERVICE_ERROR: {
            "message": "Error de servicio externo",
            "http_status": 502,
            "description": "Un servicio externo no respondió correctamente"
        },
        ErrorCode.CONFIGURATION_ERROR: {
            "message": "Error de configuración",
            "http_status": 500,
            "description": "El servicio no está configurado correctamente"
        },
        
        # Errores de Rate Limiting (429)
        ErrorCode.RATE_LIMIT_EXCEEDED: {
            "message": "Límite de tasa excedido",
            "http_status": 429,
            "description": "Ha excedido el límite de solicitudes permitidas"
        },
        ErrorCode.TOO_MANY_REQUESTS: {
            "message": "Demasiadas solicitudes",
            "http_status": 429,
            "description": "Ha realizado demasiadas solicitudes en un corto período"
        },
    }
    
    @classmethod
    def get_error(cls, error_code: ErrorCode) -> Dict[str, any]:
        """
        Obtiene información completa de un error.
        
        Args:
            error_code: Código del error
            
        Returns:
            Diccionario con código, mensaje, HTTP status y descripción
        """
        error_info = cls.ERRORS.get(error_code, cls.ERRORS[ErrorCode.INTERNAL_SERVER_ERROR])
        return {
            "code": error_code.value,
            "message": error_info["message"],
            "http_status": error_info["http_status"],
            "description": error_info["description"]
        }
    
    @classmethod
    def get_http_status(cls, error_code: ErrorCode) -> int:
        """Obtiene solo el HTTP status de un error."""
        return cls.ERRORS.get(error_code, {}).get("http_status", 500)
    
    @classmethod
    def get_message(cls, error_code: ErrorCode) -> str:
        """Obtiene solo el mensaje de un error."""
        return cls.ERRORS.get(error_code, {}).get("message", "Error desconocido")
