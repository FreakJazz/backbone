from flask import request
from flask_restx import Api, Namespace, Resource, fields

from backbone.interfaces.response_builders import (
    PaginatedResponseBuilder,
    SimpleObjectResponseBuilder,
    ProcessResponseBuilder,
    ErrorResponseBuilder,
)

from application.commands.create_product import CreateProductCommand, CreateProductCommandHandler
from application.commands.update_product import UpdateProductCommand, UpdateProductCommandHandler
from application.commands.delete_product import DeleteProductCommand, DeleteProductCommandHandler
from application.commands.change_product_status import ChangeProductStatusCommand, ChangeProductStatusCommandHandler
from application.queries.get_products import GetProductsQuery, GetProductsQueryHandler
from application.queries.get_product_by_id import GetProductByIdQuery, GetProductByIdQueryHandler


def register_routes(
    api: Api,
    create_cmd: CreateProductCommandHandler,
    update_cmd: UpdateProductCommandHandler,
    delete_cmd: DeleteProductCommandHandler,
    status_cmd: ChangeProductStatusCommandHandler,
    list_qry: GetProductsQueryHandler,
    detail_qry: GetProductByIdQueryHandler,
) -> None:
    ns = api.namespace("api/v1/products", description="Products CRUD")

    create_model = ns.model("CreateProduct", {
        "name":        fields.String(required=True, description="Product name (min 2 chars)"),
        "price":       fields.Float(required=True, description="Price > 0"),
        "category":    fields.String(required=True, description="Category"),
        "description": fields.String(description="Optional description"),
    })

    update_model = ns.model("UpdateProduct", {
        "name":        fields.String(description="Product name"),
        "price":       fields.Float(description="Price > 0"),
        "category":    fields.String(description="Category"),
        "description": fields.String(description="Description"),
    })

    status_model = ns.model("ChangeStatus", {
        "status": fields.String(required=True, description="active | inactive | discontinued"),
    })

    # ── /api/v1/products  (GET list + POST create) ────────────────────────────
    @ns.route("")
    class ProductCollection(Resource):
        @ns.doc("list_products", params={
            "filters":   {"description": "Filter token, e.g. category,eq,Electronics", "type": "string"},
            "page":      {"description": "Page number (default 1)", "type": "integer"},
            "page_size": {"description": "Items per page (default 10)", "type": "integer"},
            "sort_by":   {"description": "Sort field and dir, e.g. price:desc", "type": "string"},
        })
        def get(self):
            """List products with optional filtering, sorting and pagination."""
            try:
                query = GetProductsQuery(
                    filters=request.args.getlist("filters"),
                    sort_by=request.args.get("sort_by"),
                    page=int(request.args.get("page", 1)),
                    page_size=int(request.args.get("page_size", 10)),
                )
                result = list_qry.handle(query)
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

        @ns.expect(create_model)
        @ns.doc("create_product")
        def post(self):
            """Create a new product."""
            data = request.get_json() or {}
            try:
                cmd = CreateProductCommand(
                    name=data.get("name", ""),
                    price=data.get("price", 0),
                    category=data.get("category", ""),
                    description=data.get("description"),
                )
                product_id = create_cmd.handle(cmd)
                return ProcessResponseBuilder.created(product_id), 201
            except Exception as exc:
                err = ErrorResponseBuilder.from_exception(exc)
                return err, err["status_code"]

    # ── /api/v1/products/<id>  (GET detail + PUT update + DELETE) ────────────
    @ns.route("/<string:product_id>")
    @ns.param("product_id", "Product UUID")
    class ProductItem(Resource):
        @ns.doc("get_product")
        def get(self, product_id: str):
            """Get a single product by ID."""
            try:
                data = detail_qry.handle(GetProductByIdQuery(product_id=product_id))
                return SimpleObjectResponseBuilder.found(data), 200
            except Exception as exc:
                err = ErrorResponseBuilder.from_exception(exc)
                return err, err["status_code"]

        @ns.expect(update_model)
        @ns.doc("update_product")
        def put(self, product_id: str):
            """Update an existing product (partial update supported)."""
            data = request.get_json() or {}
            try:
                cmd = UpdateProductCommand(product_id=product_id, **{
                    k: data[k] for k in ("name", "price", "category", "description")
                    if k in data
                })
                pid = update_cmd.handle(cmd)
                return ProcessResponseBuilder.updated(pid), 200
            except Exception as exc:
                err = ErrorResponseBuilder.from_exception(exc)
                return err, err["status_code"]

        @ns.doc("delete_product")
        def delete(self, product_id: str):
            """Delete a product."""
            try:
                pid = delete_cmd.handle(DeleteProductCommand(product_id=product_id))
                return ProcessResponseBuilder.deleted(pid), 200
            except Exception as exc:
                err = ErrorResponseBuilder.from_exception(exc)
                return err, err["status_code"]

    # ── /api/v1/products/<id>/status  (PATCH) ────────────────────────────────
    @ns.route("/<string:product_id>/status")
    @ns.param("product_id", "Product UUID")
    class ProductStatus(Resource):
        @ns.expect(status_model)
        @ns.doc("change_product_status")
        def patch(self, product_id: str):
            """Change product status (active | inactive | discontinued)."""
            data = request.get_json() or {}
            try:
                cmd = ChangeProductStatusCommand(
                    product_id=product_id,
                    status=data.get("status", ""),
                )
                pid = status_cmd.handle(cmd)
                return ProcessResponseBuilder.updated(pid), 200
            except Exception as exc:
                err = ErrorResponseBuilder.from_exception(exc)
                return err, err["status_code"]
