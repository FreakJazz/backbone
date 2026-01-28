"""
Catálogo de errores centralizado para todos los microservicios
"""
from typing import Tuple


class ErrorCatalog:
    """
    Catálogo centralizado de errores
    Formato: (code: int, message: str, http_code: int)
    """
    
    # ==========================================
    # ERRORES GENERALES (1000-1999)
    # ==========================================
    INTERNAL_SERVER_ERROR: Tuple[int, str, int] = (
        1000, "Internal server error", 500
    )
    VALIDATION_ERROR: Tuple[int, str, int] = (
        1001, "Validation error", 400
    )
    NOT_FOUND: Tuple[int, str, int] = (
        1002, "Resource not found", 404
    )
    UNAUTHORIZED: Tuple[int, str, int] = (
        1003, "Unauthorized access", 401
    )
    FORBIDDEN: Tuple[int, str, int] = (
        1004, "Forbidden access", 403
    )
    BAD_REQUEST: Tuple[int, str, int] = (
        1005, "Bad request", 400
    )
    CONFLICT: Tuple[int, str, int] = (
        1006, "Resource conflict", 409
    )
    TOO_MANY_REQUESTS: Tuple[int, str, int] = (
        1007, "Too many requests", 429
    )
    
    # ==========================================
    # ERRORES DE AUTENTICACIÓN (2000-2999)
    # ==========================================
    INVALID_CREDENTIALS: Tuple[int, str, int] = (
        2000, "Invalid email or password", 401
    )
    TOKEN_EXPIRED: Tuple[int, str, int] = (
        2001, "Token has expired", 401
    )
    TOKEN_INVALID: Tuple[int, str, int] = (
        2002, "Invalid token", 401
    )
    TOKEN_MISSING: Tuple[int, str, int] = (
        2003, "Token is missing", 401
    )
    USER_ALREADY_EXISTS: Tuple[int, str, int] = (
        2004, "User already exists", 409
    )
    USER_NOT_FOUND: Tuple[int, str, int] = (
        2005, "User not found", 404
    )
    USER_INACTIVE: Tuple[int, str, int] = (
        2006, "User account is inactive", 403
    )
    USER_SUSPENDED: Tuple[int, str, int] = (
        2007, "User account is suspended", 403
    )
    EMAIL_NOT_VERIFIED: Tuple[int, str, int] = (
        2008, "Email not verified", 403
    )
    INVALID_REFRESH_TOKEN: Tuple[int, str, int] = (
        2009, "Invalid refresh token", 401
    )
    PASSWORD_TOO_WEAK: Tuple[int, str, int] = (
        2010, "Password does not meet requirements", 400
    )
    
    # ==========================================
    # ERRORES DE CONDUCTOR (3000-3999)
    # ==========================================
    DRIVER_NOT_FOUND: Tuple[int, str, int] = (
        3000, "Driver not found", 404
    )
    DRIVER_NOT_VERIFIED: Tuple[int, str, int] = (
        3001, "Driver not verified", 403
    )
    DRIVER_LICENSE_EXPIRED: Tuple[int, str, int] = (
        3002, "Driver license has expired", 403
    )
    DRIVER_NOT_AVAILABLE: Tuple[int, str, int] = (
        3003, "Driver is not available", 409
    )
    DRIVER_ALREADY_ON_TRIP: Tuple[int, str, int] = (
        3004, "Driver is already on a trip", 409
    )
    DRIVER_LOW_RATING: Tuple[int, str, int] = (
        3005, "Driver rating is below minimum required", 403
    )
    INVALID_DRIVER_DOCUMENT: Tuple[int, str, int] = (
        3006, "Invalid or missing driver document", 400
    )
    
    # ==========================================
    # ERRORES DE VIAJES (4000-4999)
    # ==========================================
    TRIP_NOT_FOUND: Tuple[int, str, int] = (
        4000, "Trip not found", 404
    )
    TRIP_ALREADY_CANCELLED: Tuple[int, str, int] = (
        4001, "Trip already cancelled", 409
    )
    TRIP_ALREADY_COMPLETED: Tuple[int, str, int] = (
        4002, "Trip already completed", 409
    )
    TRIP_CANNOT_BE_CANCELLED: Tuple[int, str, int] = (
        4003, "Trip cannot be cancelled at this stage", 409
    )
    TRIP_DURATION_EXCEEDED: Tuple[int, str, int] = (
        4004, "Trip duration exceeds maximum allowed (5 hours)", 400
    )
    INVALID_ROUTE: Tuple[int, str, int] = (
        4005, "Invalid route configuration", 400
    )
    NO_DRIVERS_AVAILABLE: Tuple[int, str, int] = (
        4006, "No drivers available for this route", 404
    )
    
    # ==========================================
    # ERRORES DE RESERVAS (5000-5999)
    # ==========================================
    BOOKING_NOT_FOUND: Tuple[int, str, int] = (
        5000, "Booking not found", 404
    )
    BOOKING_ALREADY_EXISTS: Tuple[int, str, int] = (
        5001, "Active booking already exists", 409
    )
    BOOKING_EXPIRED: Tuple[int, str, int] = (
        5002, "Booking has expired", 410
    )
    BOOKING_CANNOT_BE_MODIFIED: Tuple[int, str, int] = (
        5003, "Booking cannot be modified at this stage", 409
    )
    BOOKING_TIME_CONFLICT: Tuple[int, str, int] = (
        5004, "Booking time conflicts with existing reservation", 409
    )
    
    # ==========================================
    # ERRORES DE GEOLOCALIZACIÓN (6000-6999)
    # ==========================================
    INVALID_COORDINATES: Tuple[int, str, int] = (
        6000, "Invalid coordinates", 400
    )
    LOCATION_NOT_FOUND: Tuple[int, str, int] = (
        6001, "Location not found", 404
    )
    CITY_NOT_SUPPORTED: Tuple[int, str, int] = (
        6002, "City is not supported for this service", 400
    )
    ORIGIN_DESTINATION_SAME: Tuple[int, str, int] = (
        6003, "Origin and destination cannot be the same", 400
    )
    DISTANCE_CALCULATION_ERROR: Tuple[int, str, int] = (
        6004, "Error calculating distance", 500
    )
    ROUTE_NOT_FOUND: Tuple[int, str, int] = (
        6005, "Route not found", 404
    )
    
    # ==========================================
    # ERRORES DE PAGOS (7000-7999)
    # ==========================================
    PAYMENT_FAILED: Tuple[int, str, int] = (
        7000, "Payment failed", 402
    )
    PAYMENT_METHOD_INVALID: Tuple[int, str, int] = (
        7001, "Invalid payment method", 400
    )
    INSUFFICIENT_FUNDS: Tuple[int, str, int] = (
        7002, "Insufficient funds", 402
    )
    PAYMENT_ALREADY_PROCESSED: Tuple[int, str, int] = (
        7003, "Payment already processed", 409
    )
    REFUND_FAILED: Tuple[int, str, int] = (
        7004, "Refund failed", 500
    )
    
    # ==========================================
    # ERRORES DE RATINGS (8000-8999)
    # ==========================================
    RATING_ALREADY_EXISTS: Tuple[int, str, int] = (
        8000, "Rating already exists for this trip", 409
    )
    INVALID_RATING_VALUE: Tuple[int, str, int] = (
        8001, "Invalid rating value (must be between 1 and 5)", 400
    )
    CANNOT_RATE_OWN_TRIP: Tuple[int, str, int] = (
        8002, "Cannot rate your own trip", 403
    )
    TRIP_NOT_COMPLETED_FOR_RATING: Tuple[int, str, int] = (
        8003, "Trip must be completed before rating", 409
    )
    
    # ==========================================
    # ERRORES DE BASE DE DATOS (9000-9999)
    # ==========================================
    DATABASE_ERROR: Tuple[int, str, int] = (
        9000, "Database error", 500
    )
    DATABASE_CONNECTION_ERROR: Tuple[int, str, int] = (
        9001, "Database connection error", 500
    )
    DUPLICATE_ENTRY: Tuple[int, str, int] = (
        9002, "Duplicate entry", 409
    )
    FOREIGN_KEY_CONSTRAINT: Tuple[int, str, int] = (
        9003, "Foreign key constraint violation", 409
    )
    
    @staticmethod
    def get_error_details(error_tuple: Tuple[int, str, int]):
        """
        Extrae los detalles del error
        
        Args:
            error_tuple: Tupla de error (code, message, http_code)
            
        Returns:
            Dict con code, message y http_code
        """
        code, message, http_code = error_tuple
        return {
            "code": code,
            "message": message,
            "http_code": http_code
        }
    
    @staticmethod
    def format_error_response(error_tuple: Tuple[int, str, int], details: str = None):
        """
        Formatea una respuesta de error
        
        Args:
            error_tuple: Tupla de error
            details: Detalles adicionales del error
            
        Returns:
            Dict con la respuesta de error formateada
        """
        code, message, http_code = error_tuple
        response = {
            "success": False,
            "error_code": code,
            "message": message,
            "details": details
        }
        return response, http_code
