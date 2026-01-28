"""
Events module initialization
"""
from .event_schemas import (
    BaseEvent,
    # User Events
    UserRegisteredEvent,
    UserUpdatedEvent,
    UserDeletedEvent,
    # Driver Events
    DriverRegisteredEvent,
    DriverVerifiedEvent,
    DriverDocumentUploadedEvent,
    DriverLocationUpdatedEvent,
    DriverAvailabilityChangedEvent,
    # Trip Events
    TripRequestedEvent,
    TripAcceptedEvent,
    TripStartedEvent,
    TripCompletedEvent,
    TripCancelledEvent,
    # Booking Events
    BookingCreatedEvent,
    BookingConfirmedEvent,
    BookingCancelledEvent,
    BookingExpiredEvent,
    # Payment Events
    PaymentInitiatedEvent,
    PaymentCompletedEvent,
    PaymentFailedEvent,
    PaymentRefundedEvent,
    # Rating Events
    RatingSubmittedEvent,
    # Notification Events
    NotificationSendEvent,
    EmailSendEvent,
    SMSSendEvent,
    PushNotificationSendEvent,
)

__all__ = [
    "BaseEvent",
    # User Events
    "UserRegisteredEvent",
    "UserUpdatedEvent",
    "UserDeletedEvent",
    # Driver Events
    "DriverRegisteredEvent",
    "DriverVerifiedEvent",
    "DriverDocumentUploadedEvent",
    "DriverLocationUpdatedEvent",
    "DriverAvailabilityChangedEvent",
    # Trip Events
    "TripRequestedEvent",
    "TripAcceptedEvent",
    "TripStartedEvent",
    "TripCompletedEvent",
    "TripCancelledEvent",
    # Booking Events
    "BookingCreatedEvent",
    "BookingConfirmedEvent",
    "BookingCancelledEvent",
    "BookingExpiredEvent",
    # Payment Events
    "PaymentInitiatedEvent",
    "PaymentCompletedEvent",
    "PaymentFailedEvent",
    "PaymentRefundedEvent",
    # Rating Events
    "RatingSubmittedEvent",
    # Notification Events
    "NotificationSendEvent",
    "EmailSendEvent",
    "SMSSendEvent",
    "PushNotificationSendEvent",
]
