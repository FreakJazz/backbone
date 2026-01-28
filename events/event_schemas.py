"""
Esquemas de eventos compartidos entre microservicios
Estos eventos se publican a través de RabbitMQ
"""
from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from shared.common.constants import EventTypes


# ==========================================
# BASE EVENT
# ==========================================
class BaseEvent(BaseModel):
    """Evento base para todos los eventos del sistema"""
    event_id: str = Field(..., description="ID único del evento")
    event_type: str = Field(..., description="Tipo de evento")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    source_service: str = Field(..., description="Servicio que genera el evento")
    correlation_id: Optional[str] = Field(None, description="ID de correlación para trazabilidad")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


# ==========================================
# EVENTOS DE USUARIOS
# ==========================================
class UserRegisteredEvent(BaseEvent):
    """Evento: Usuario registrado"""
    event_type: str = EventTypes.USER_REGISTERED
    user_id: str
    email: str
    full_name: str
    role: str
    phone: Optional[str] = None


class UserUpdatedEvent(BaseEvent):
    """Evento: Usuario actualizado"""
    event_type: str = EventTypes.USER_UPDATED
    user_id: str
    updated_fields: Dict[str, Any]


class UserDeletedEvent(BaseEvent):
    """Evento: Usuario eliminado"""
    event_type: str = EventTypes.USER_DELETED
    user_id: str
    reason: Optional[str] = None


# ==========================================
# EVENTOS DE CONDUCTORES
# ==========================================
class DriverRegisteredEvent(BaseEvent):
    """Evento: Conductor registrado"""
    event_type: str = EventTypes.DRIVER_REGISTERED
    driver_id: str
    user_id: str
    vehicle_info: Dict[str, Any]


class DriverVerifiedEvent(BaseEvent):
    """Evento: Conductor verificado"""
    event_type: str = EventTypes.DRIVER_VERIFIED
    driver_id: str
    user_id: str
    verification_date: datetime
    verified_by: str


class DriverDocumentUploadedEvent(BaseEvent):
    """Evento: Documento de conductor subido"""
    event_type: str = EventTypes.DRIVER_DOCUMENT_UPLOADED
    driver_id: str
    document_type: str
    document_url: str
    requires_verification: bool = True


class DriverLocationUpdatedEvent(BaseEvent):
    """Evento: Ubicación de conductor actualizada"""
    event_type: str = EventTypes.DRIVER_LOCATION_UPDATED
    driver_id: str
    latitude: float
    longitude: float
    timestamp: datetime
    heading: Optional[float] = None
    speed: Optional[float] = None


class DriverAvailabilityChangedEvent(BaseEvent):
    """Evento: Disponibilidad de conductor cambiada"""
    event_type: str = EventTypes.DRIVER_AVAILABILITY_CHANGED
    driver_id: str
    is_available: bool
    city: Optional[str] = None


# ==========================================
# EVENTOS DE VIAJES
# ==========================================
class TripRequestedEvent(BaseEvent):
    """Evento: Viaje solicitado"""
    event_type: str = EventTypes.TRIP_REQUESTED
    trip_id: str
    passenger_id: str
    origin_city: str
    destination_city: str
    pickup_location: Dict[str, float]  # {"latitude": x, "longitude": y}
    dropoff_location: Dict[str, float]
    estimated_price: float
    estimated_duration_minutes: int


class TripAcceptedEvent(BaseEvent):
    """Evento: Viaje aceptado"""
    event_type: str = EventTypes.TRIP_ACCEPTED
    trip_id: str
    driver_id: str
    passenger_id: str
    acceptance_time: datetime


class TripStartedEvent(BaseEvent):
    """Evento: Viaje iniciado"""
    event_type: str = EventTypes.TRIP_STARTED
    trip_id: str
    driver_id: str
    passenger_id: str
    start_time: datetime
    start_location: Dict[str, float]


class TripCompletedEvent(BaseEvent):
    """Evento: Viaje completado"""
    event_type: str = EventTypes.TRIP_COMPLETED
    trip_id: str
    driver_id: str
    passenger_id: str
    start_time: datetime
    end_time: datetime
    final_price: float
    distance_km: float
    duration_minutes: int


class TripCancelledEvent(BaseEvent):
    """Evento: Viaje cancelado"""
    event_type: str = EventTypes.TRIP_CANCELLED
    trip_id: str
    cancelled_by: str  # user_id
    cancelled_by_role: str  # "driver" o "passenger"
    cancellation_reason: Optional[str] = None
    cancellation_time: datetime


# ==========================================
# EVENTOS DE RESERVAS
# ==========================================
class BookingCreatedEvent(BaseEvent):
    """Evento: Reserva creada"""
    event_type: str = EventTypes.BOOKING_CREATED
    booking_id: str
    passenger_id: str
    route_code: str
    pickup_datetime: datetime
    estimated_price: float


class BookingConfirmedEvent(BaseEvent):
    """Evento: Reserva confirmada"""
    event_type: str = EventTypes.BOOKING_CONFIRMED
    booking_id: str
    driver_id: str
    confirmation_time: datetime


class BookingCancelledEvent(BaseEvent):
    """Evento: Reserva cancelada"""
    event_type: str = EventTypes.BOOKING_CANCELLED
    booking_id: str
    cancelled_by: str
    cancellation_reason: Optional[str] = None


class BookingExpiredEvent(BaseEvent):
    """Evento: Reserva expirada"""
    event_type: str = EventTypes.BOOKING_EXPIRED
    booking_id: str
    expiration_time: datetime


# ==========================================
# EVENTOS DE PAGOS
# ==========================================
class PaymentInitiatedEvent(BaseEvent):
    """Evento: Pago iniciado"""
    event_type: str = EventTypes.PAYMENT_INITIATED
    payment_id: str
    trip_id: str
    passenger_id: str
    amount: float
    payment_method: str


class PaymentCompletedEvent(BaseEvent):
    """Evento: Pago completado"""
    event_type: str = EventTypes.PAYMENT_COMPLETED
    payment_id: str
    trip_id: str
    passenger_id: str
    driver_id: str
    amount: float
    payment_method: str
    transaction_id: str
    completion_time: datetime


class PaymentFailedEvent(BaseEvent):
    """Evento: Pago fallido"""
    event_type: str = EventTypes.PAYMENT_FAILED
    payment_id: str
    trip_id: str
    passenger_id: str
    amount: float
    failure_reason: str


class PaymentRefundedEvent(BaseEvent):
    """Evento: Pago reembolsado"""
    event_type: str = EventTypes.PAYMENT_REFUNDED
    payment_id: str
    trip_id: str
    refund_amount: float
    refund_reason: str
    refund_time: datetime


# ==========================================
# EVENTOS DE RATINGS
# ==========================================
class RatingSubmittedEvent(BaseEvent):
    """Evento: Calificación enviada"""
    event_type: str = EventTypes.RATING_SUBMITTED
    rating_id: str
    trip_id: str
    rated_by: str  # user_id
    rated_user: str  # user_id
    score: float
    comment: Optional[str] = None


# ==========================================
# EVENTOS DE NOTIFICACIONES
# ==========================================
class NotificationSendEvent(BaseEvent):
    """Evento: Enviar notificación"""
    event_type: str = EventTypes.NOTIFICATION_SEND
    recipient_id: str
    notification_type: str  # email, sms, push
    title: str
    message: str
    data: Optional[Dict[str, Any]] = None


class EmailSendEvent(BaseEvent):
    """Evento: Enviar email"""
    event_type: str = EventTypes.EMAIL_SEND
    recipient_email: str
    subject: str
    body: str
    template: Optional[str] = None
    template_data: Optional[Dict[str, Any]] = None


class SMSSendEvent(BaseEvent):
    """Evento: Enviar SMS"""
    event_type: str = EventTypes.SMS_SEND
    recipient_phone: str
    message: str


class PushNotificationSendEvent(BaseEvent):
    """Evento: Enviar notificación push"""
    event_type: str = EventTypes.PUSH_NOTIFICATION_SEND
    recipient_id: str
    title: str
    body: str
    data: Optional[Dict[str, Any]] = None
    badge: Optional[int] = None
