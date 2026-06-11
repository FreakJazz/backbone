"""HTTP handler for GET /api/v1/products/<id> — Interfaces / HTTP / Queries"""
from flask import request, jsonify
from typing import Dict, Any
import sys, os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../..')))

from backbone.interfaces.response_builders import (
    SimpleObjectResponseBuilder, ErrorResponseBuilder,
)
from examples.clean_api_python.application.queries.get_product_by_id import (
    GetProductByIDQuery, GetProductByIDQueryHandler,
)


class GetProductByIDHttpHandler:
    """GET /api/v1/products/<id> → raw product object  HTTP 200"""

    def __init__(self, handler: GetProductByIDQueryHandler):
        self.handler = handler

    def handle(self, product_id: str):
        query = GetProductByIDQuery(id=product_id)

        try:
            result = self.handler.handle(query, self._ctx())
        except Exception as e:
            resp = ErrorResponseBuilder.internal_server_error(str(e))
            return jsonify(resp), resp["status_code"]

        if result is None:
            resp = ErrorResponseBuilder.not_found_error("Product not found")
            return jsonify(resp), resp["status_code"]

        return jsonify(SimpleObjectResponseBuilder.found(result.product.to_dict())), 200

    @staticmethod
    def _ctx() -> Dict[str, Any]:
        return {
            "request_id": request.headers.get("X-Request-ID", "unknown"),
            "user_id":    request.headers.get("X-User-ID", "unknown"),
        }
