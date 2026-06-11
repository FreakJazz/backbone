"""HTTP handler for PUT /api/v1/products/<id> — Interfaces / HTTP / Commands"""
from flask import request, jsonify
from typing import Dict, Any
import sys, os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../..')))

from backbone.interfaces.response_builders import ProcessResponseBuilder, ErrorResponseBuilder
from examples.clean_api_python.application.commands.update_product import (
    UpdateProductCommand, UpdateProductCommandHandler,
)

_NOT_FOUND = "not found"


class UpdateProductHttpHandler:
    """PUT /api/v1/products/<id> → {"id": "uuid"}  HTTP 200"""

    def __init__(self, handler: UpdateProductCommandHandler):
        self.handler = handler

    def handle(self, product_id: str):
        try:
            data = request.get_json(force=True)
            cmd = UpdateProductCommand(
                id=product_id,
                name=data.get("name"),
                description=data.get("description"),
                price=float(data["price"]) if "price" in data else None,
                category=data.get("category"),
                stock=int(data["stock"]) if "stock" in data else None,
            )
        except Exception:
            resp = ErrorResponseBuilder.validation_error("Invalid JSON payload")
            return jsonify(resp), resp["status_code"]

        try:
            result = self.handler.handle(cmd, self._ctx())
        except ValueError as e:
            msg = str(e)
            resp = (
                ErrorResponseBuilder.not_found_error(msg)
                if _NOT_FOUND in msg.lower()
                else ErrorResponseBuilder.validation_error(msg)
            )
            return jsonify(resp), resp["status_code"]

        return jsonify(ProcessResponseBuilder.updated(result.product_id)), 200

    @staticmethod
    def _ctx() -> Dict[str, Any]:
        return {
            "request_id": request.headers.get("X-Request-ID", "unknown"),
            "user_id":    request.headers.get("X-User-ID", "unknown"),
        }
