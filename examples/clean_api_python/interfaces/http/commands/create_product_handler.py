"""HTTP handler for POST /api/v1/products — Interfaces / HTTP / Commands"""
from flask import request, jsonify
from typing import Dict, Any
import sys, os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../..')))

from backbone.interfaces.response_builders import ProcessResponseBuilder, ErrorResponseBuilder
from examples.clean_api_python.application.commands.create_product import (
    CreateProductCommand, CreateProductCommandHandler,
)


class CreateProductHttpHandler:
    """POST /api/v1/products → {"id": "uuid"}  HTTP 201"""

    def __init__(self, handler: CreateProductCommandHandler):
        self.handler = handler

    def handle(self):
        try:
            data = request.get_json(force=True)
            cmd = CreateProductCommand(
                name=data.get("name"),
                description=data.get("description", ""),
                price=float(data.get("price", 0)),
                category=data.get("category"),
                stock=int(data.get("stock", 0)),
            )
        except Exception:
            resp = ErrorResponseBuilder.validation_error("Invalid JSON payload")
            return jsonify(resp), resp["status_code"]

        try:
            result = self.handler.handle(cmd, self._ctx())
        except Exception as e:
            resp = ErrorResponseBuilder.validation_error(str(e))
            return jsonify(resp), resp["status_code"]

        return jsonify(ProcessResponseBuilder.created(result.product_id)), 201

    @staticmethod
    def _ctx() -> Dict[str, Any]:
        return {
            "request_id": request.headers.get("X-Request-ID", "unknown"),
            "user_id":    request.headers.get("X-User-ID", "unknown"),
        }
