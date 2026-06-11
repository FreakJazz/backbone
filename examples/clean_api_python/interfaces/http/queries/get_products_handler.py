"""HTTP handler for GET /api/v1/products — Interfaces / HTTP / Queries"""
from flask import request, jsonify
from typing import Dict, Any
import sys, os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../..')))

from backbone.interfaces.response_builders import PaginatedResponseBuilder, ErrorResponseBuilder
from examples.clean_api_python.application.queries.get_products import (
    GetProductsQuery, GetProductsQueryHandler,
)


class GetProductsHttpHandler:
    """
    GET /api/v1/products → paginated envelope  HTTP 200

    Query params:
      filters   — repeated: "field,operator,value[,condition]"
      page      — page number (default 1)
      page_size — items per page (default 10)
      sort_by   — "field:direction"  e.g. price:desc
    """

    def __init__(self, handler: GetProductsQueryHandler):
        self.handler = handler

    def handle(self):
        query = GetProductsQuery(
            filters=request.args.getlist("filters"),
            page=int(request.args.get("page", 1)),
            page_size=int(request.args.get("page_size", 10)),
            sort_by=request.args.get("sort_by", "created_at:desc"),
        )

        try:
            result = self.handler.handle(query, self._ctx())
        except Exception as e:
            resp = ErrorResponseBuilder.internal_server_error(str(e))
            return jsonify(resp), resp["status_code"]

        resp = PaginatedResponseBuilder.success(
            items=[p.to_dict() for p in result.products],
            total_count=result.total_count,
            page=result.page,
            page_size=result.page_size,
            message="Products retrieved successfully",
        )
        return jsonify(resp), 200

    @staticmethod
    def _ctx() -> Dict[str, Any]:
        return {
            "request_id": request.headers.get("X-Request-ID", "unknown"),
            "user_id":    request.headers.get("X-User-ID", "unknown"),
        }
