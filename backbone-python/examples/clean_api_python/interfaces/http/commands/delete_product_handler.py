"""HTTP handler for DELETE /api/v1/products/<id> — Interfaces / HTTP / Commands"""
from flask import request, jsonify
from typing import Dict, Any
import sys, os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../..')))

from backbone.interfaces.response_builders import ProcessResponseBuilder, ErrorResponseBuilder
from examples.clean_api_python.application.commands.delete_product import (
    DeleteProductCommand, DeleteProductCommandHandler,
)

_NOT_FOUND = "not found"


class DeleteProductHttpHandler:
    """DELETE /api/v1/products/<id> → {"id": "uuid"}  HTTP 200"""

    def __init__(self, handler: DeleteProductCommandHandler):
        self.handler = handler

    def handle(self, product_id: str):
        try:
            self.handler.handle(DeleteProductCommand(id=product_id), self._ctx())
        except ValueError as e:
            msg = str(e)
            resp = (
                ErrorResponseBuilder.not_found_error(msg)
                if _NOT_FOUND in msg.lower()
                else ErrorResponseBuilder.internal_server_error(msg)
            )
            return jsonify(resp), resp["status_code"]

        return jsonify(ProcessResponseBuilder.deleted(product_id)), 200

    @staticmethod
    def _ctx() -> Dict[str, Any]:
        return {
            "request_id": request.headers.get("X-Request-ID", "unknown"),
            "user_id":    request.headers.get("X-User-ID", "unknown"),
        }
