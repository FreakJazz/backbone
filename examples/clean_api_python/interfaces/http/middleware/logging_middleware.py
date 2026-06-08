"""Logging middleware for Flask"""
from flask import request, g
from functools import wraps
import time
import uuid
import sys
import os

# Add backbone to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../..')))

from backbone.infrastructure.logging import LoggerFactory, LogLevel


logger = LoggerFactory.create_layer_logger(
    "product-api",
    "interfaces",
    "HTTPMiddleware"
)


def logging_middleware(f):
    """Logs HTTP requests and responses"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        start = time.time()
        
        # Generate request ID
        request_id = str(uuid.uuid4())
        g.request_id = request_id
        
        # Log request
        logger.log(
            LogLevel.INFO,
            "Incoming HTTP request",
            extra_data={
                "method": request.method,
                "path": request.path,
                "query": request.query_string.decode(),
                "remote_ip": request.remote_addr,
                "user_agent": request.user_agent.string
            },
            context={"request_id": request_id}
        )
        
        # Call handler
        response = f(*args, **kwargs)
        
        # Calculate duration
        duration_ms = int((time.time() - start) * 1000)
        
        # Get status code
        if isinstance(response, tuple):
            status_code = response[1]
        else:
            status_code = 200
        
        # Log response
        logger.log(
            LogLevel.INFO,
            "HTTP request completed",
            extra_data={
                "method": request.method,
                "path": request.path,
                "status_code": status_code,
                "duration_ms": duration_ms
            },
            context={"request_id": request_id}
        )
        
        return response
    
    return decorated_function
