"""
Constantes compartidas entre microservicios
"""
from enum import Enum


# ==========================================
# CONSTANTES DE NEGOCIO - ECUADOR
# ==========================================
class BusinessConstants:
    """Constantes del negocio"""
    
    # Duración máxima de viaje
    MAX_TRIP_DURATION_HOURS = 5
    MAX_TRIP_DURATION_MINUTES = 300
    
    # Ciudades principales
    PRIMARY_CITIES = ["Quito", "Guayaquil", "Cuenca"]
    
    # Ciudades secundarias
    SECONDARY_CITIES = [
        "Ambato", "Riobamba", "Ibarra", "Manta", 
        "Santo Domingo", "Machala", "Loja", "Esmeraldas",
        "Latacunga", "Portoviejo", "Quevedo", "Tulcán"
    ]
    
    # Rating mínimo
    MIN_DRIVER_RATING = 4.0
    MIN_PASSENGER_RATING = 3.5
    
    # Configuración de precios
    BASE_FARE_USD = 5.00
    PRICE_PER_KM = 0.50
    PRICE_PER_MINUTE = 0.15
    PLATFORM_COMMISSION_PERCENT = 15
    MIN_TRIP_PRICE = 5.00
    
    # Radio de búsqueda
    DEFAULT_SEARCH_RADIUS_KM = 50
    MAX_SEARCH_RADIUS_KM = 300
    
    # Tiempo de expiración de reservas (minutos)
    BOOKING_EXPIRATION_MINUTES = 15
    
    # Tiempo máximo de espera para conductor (minutos)
    MAX_DRIVER_WAIT_TIME_MINUTES = 10
    
    # Distancia máxima para pickup (km)
    MAX_PICKUP_DISTANCE_KM = 10


# ==========================================
# CONSTANTES DE JWT
# ==========================================
class JWTConstants:
    """Constantes de JWT"""
    ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = 30
    REFRESH_TOKEN_EXPIRE_DAYS = 7
    TOKEN_TYPE = "bearer"


# ==========================================
# CONSTANTES DE CACHÉ (REDIS)
# ==========================================
class CacheKeys:
    """Claves de Redis"""
    
    # Sesiones de usuario
    USER_SESSION = "user:session:{user_id}"
    
    # Ubicación de conductores
    DRIVER_LOCATION = "driver:location:{driver_id}"
    DRIVERS_NEARBY = "drivers:nearby:{lat}:{lon}:{radius}"
    
    # Disponibilidad de conductores
    DRIVER_AVAILABILITY = "driver:availability:{driver_id}"
    AVAILABLE_DRIVERS = "drivers:available:{city}"
    
    # Viajes activos
    ACTIVE_TRIP = "trip:active:{trip_id}"
    USER_ACTIVE_TRIP = "user:active_trip:{user_id}"
    DRIVER_ACTIVE_TRIP = "driver:active_trip:{driver_id}"
    
    # Cache de rutas
    ROUTE_CACHE = "cache:route:{origin}:{destination}"
    ROUTE_CATALOG = "cache:routes:all"
    
    # Rate limiting
    RATE_LIMIT = "rate:limit:{ip}:{endpoint}"
    
    # TTL (Time To Live) en segundos
    TTL_SHORT = 300  # 5 minutos
    TTL_MEDIUM = 1800  # 30 minutos
    TTL_LONG = 3600  # 1 hora
    TTL_DAY = 86400  # 24 horas


# ==========================================
# CONSTANTES DE EVENTOS (RABBITMQ)
# ==========================================
class EventTypes:
    """Tipos de eventos del sistema"""
    
    # Eventos de usuarios
    USER_REGISTERED = "user.registered"
    USER_UPDATED = "user.updated"
    USER_DELETED = "user.deleted"
    
    # Eventos de conductores
    DRIVER_REGISTERED = "driver.registered"
    DRIVER_VERIFIED = "driver.verified"
    DRIVER_DOCUMENT_UPLOADED = "driver.document.uploaded"
    DRIVER_LOCATION_UPDATED = "driver.location.updated"
    DRIVER_AVAILABILITY_CHANGED = "driver.availability.changed"
    
    # Eventos de viajes
    TRIP_REQUESTED = "trip.requested"
    TRIP_ACCEPTED = "trip.accepted"
    TRIP_STARTED = "trip.started"
    TRIP_COMPLETED = "trip.completed"
    TRIP_CANCELLED = "trip.cancelled"
    
    # Eventos de reservas
    BOOKING_CREATED = "booking.created"
    BOOKING_CONFIRMED = "booking.confirmed"
    BOOKING_CANCELLED = "booking.cancelled"
    BOOKING_EXPIRED = "booking.expired"
    
    # Eventos de pagos
    PAYMENT_INITIATED = "payment.initiated"
    PAYMENT_COMPLETED = "payment.completed"
    PAYMENT_FAILED = "payment.failed"
    PAYMENT_REFUNDED = "payment.refunded"
    
    # Eventos de ratings
    RATING_SUBMITTED = "rating.submitted"
    
    # Eventos de notificaciones
    NOTIFICATION_SEND = "notification.send"
    EMAIL_SEND = "email.send"
    SMS_SEND = "sms.send"
    PUSH_NOTIFICATION_SEND = "push.send"


class QueueNames:
    """Nombres de colas de RabbitMQ"""
    
    # Colas por servicio
    AUTH_QUEUE = "auth_service_queue"
    TRIP_QUEUE = "trip_service_queue"
    NOTIFICATION_QUEUE = "notification_service_queue"
    PAYMENT_QUEUE = "payment_service_queue"
    
    # Colas de eventos
    USER_EVENTS = "user_events"
    DRIVER_EVENTS = "driver_events"
    TRIP_EVENTS = "trip_events"
    BOOKING_EVENTS = "booking_events"
    PAYMENT_EVENTS = "payment_events"


class ExchangeNames:
    """Nombres de exchanges de RabbitMQ"""
    MAIN_EXCHANGE = "ajms_exchange"
    USER_EXCHANGE = "user_exchange"
    TRIP_EXCHANGE = "trip_exchange"
    NOTIFICATION_EXCHANGE = "notification_exchange"


# ==========================================
# CONSTANTES DE VALIDACIÓN
# ==========================================
class ValidationConstants:
    """Constantes de validación"""
    
    # Contraseñas
    PASSWORD_MIN_LENGTH = 8
    PASSWORD_MAX_LENGTH = 128
    
    # Nombres
    NAME_MIN_LENGTH = 2
    NAME_MAX_LENGTH = 100
    
    # Email
    EMAIL_MAX_LENGTH = 255
    
    # Teléfono (Ecuador)
    PHONE_REGEX = r"^(09|\+593)[0-9]{8}$"
    
    # Cédula Ecuador (10 dígitos)
    CEDULA_LENGTH = 10
    
    # Comentarios
    COMMENT_MAX_LENGTH = 500
    
    # Rating
    RATING_MIN = 1.0
    RATING_MAX = 5.0
    
    # Coordenadas Ecuador (aproximado)
    ECUADOR_LAT_MIN = -5.0
    ECUADOR_LAT_MAX = 1.5
    ECUADOR_LON_MIN = -81.0
    ECUADOR_LON_MAX = -75.0


# ==========================================
# CONSTANTES DE PAGINACIÓN
# ==========================================
class PaginationConstants:
    """Constantes de paginación"""
    DEFAULT_PAGE = 1
    DEFAULT_PAGE_SIZE = 20
    MAX_PAGE_SIZE = 100


# ==========================================
# CONSTANTES DE ARCHIVOS
# ==========================================
class FileConstants:
    """Constantes de archivos"""
    
    # Tipos de archivo permitidos para documentos
    ALLOWED_DOCUMENT_TYPES = [
        "image/jpeg", "image/png", "image/jpg",
        "application/pdf"
    ]
    
    # Tamaño máximo de archivo (5 MB)
    MAX_FILE_SIZE_MB = 5
    MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024
    
    # Tipos de documentos
    DOCUMENT_TYPES = [
        "cedula", "passport", "license", 
        "vehicle_registration", "insurance"
    ]


# ==========================================
# HEADERS PERSONALIZADOS
# ==========================================
class CustomHeaders:
    """Headers personalizados de la aplicación"""
    TENANT_ID = "X-Tenant-Id"
    SOURCE_NAME = "X-Source-Name"
    CULTURE_REGION = "X-Culture-Region"
    REQUEST_ID = "X-Request-Id"
    CLIENT_VERSION = "X-Client-Version"


# ==========================================
# TIMEZONE
# ==========================================
class TimezoneConstants:
    """Constantes de zona horaria"""
    ECUADOR_TIMEZONE = "America/Guayaquil"
    UTC_OFFSET = -5  # Ecuador es UTC-5
