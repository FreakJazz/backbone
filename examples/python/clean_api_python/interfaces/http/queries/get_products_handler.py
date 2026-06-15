from flask import request
from flask_restx import Namespace, Resource

from backbone.interfaces.response_builders import PaginatedResponseBuilder, ErrorResponseBuilder

from application.queries.get_products import GetProductsQuery, GetProductsQueryHandler


def register(namespace: Namespace, handler: GetProductsQueryHandler) -> None:
    @namespace.route("")
    class ProductList(Resource):
        @namespace.doc("list_products", params={
            "filters":   {"description": "e.g. category,eq,Electronics,and", "type": "string"},
            "page":      {"description": "Page number (default 1)", "type": "integer"},
            "page_size": {"description": "Items per page (default 10)", "type": "integer"},
            "sort_by":   {"description": "e.g. price:desc", "type": "string"},
        })
        def get(self):
            try:
                query = GetProductsQuery(
                    filters=request.args.getlist("filters"),
                    sort_by=request.args.get("sort_by"),
                    page=int(request.args.get("page", 1)),
                    page_size=int(request.args.get("page_size", 10)),
                )
                result = handler.handle(query)
                return PaginatedResponseBuilder.success(
                    items=result.items,
                    total_count=result.total_count,
                    page=result.page,
                    page_size=result.page_size,
                    message="Products retrieved successfully",
                ), 200
            except Exception as exc:
                err = ErrorResponseBuilder.from_exception(exc)
                return err, err["status_code"]
