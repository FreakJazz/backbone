from flask import request
from flask_restx import Api, Namespace, Resource, fields

from backbone.interfaces.response_builders import (
    PaginatedResponseBuilder,
    CursorPaginatedResponseBuilder,
    SimpleObjectResponseBuilder,
    ProcessResponseBuilder,
    ErrorResponseBuilder,
)

from application.commands.create_product import CreateProductCommand, CreateProductCommandHandler
from application.commands.update_product import UpdateProductCommand, UpdateProductCommandHandler
from application.commands.delete_product import DeleteProductCommand, DeleteProductCommandHandler
from application.commands.change_product_status import ChangeProductStatusCommand, ChangeProductStatusCommandHandler
from application.commands.register_sale import RegisterSaleCommand, RegisterSaleCommandHandler
from application.commands.register_stock_movement import RegisterStockMovementCommand, RegisterStockMovementCommandHandler
from application.queries.get_products import GetProductsQuery, GetProductsQueryHandler
from application.queries.get_products_page import GetProductsPageQuery, GetProductsPageQueryHandler
from application.queries.get_product_by_id import GetProductByIdQuery, GetProductByIdQueryHandler
from application.queries.get_sales import GetSalesQuery, GetSalesQueryHandler
from application.queries.get_stock_movements import GetStockMovementsQuery, GetStockMovementsQueryHandler


def register_routes(
    api: Api,
    create_cmd: CreateProductCommandHandler,
    update_cmd: UpdateProductCommandHandler,
    delete_cmd: DeleteProductCommandHandler,
    status_cmd: ChangeProductStatusCommandHandler,
    list_qry: GetProductsQueryHandler,
    page_qry: GetProductsPageQueryHandler,
    detail_qry: GetProductByIdQueryHandler,
    register_sale_cmd: RegisterSaleCommandHandler,
    list_sales_qry: GetSalesQueryHandler,
    register_movement_cmd: RegisterStockMovementCommandHandler,
    list_movements_qry: GetStockMovementsQueryHandler,
) -> None:
    _register_error_handler(api)
    _register_product_routes(api, create_cmd, update_cmd, delete_cmd, status_cmd, list_qry, page_qry, detail_qry)
    _register_sale_routes(api, register_sale_cmd, list_sales_qry)
    _register_stock_movement_routes(api, register_movement_cmd, list_movements_qry)


def _register_error_handler(api: Api) -> None:
    """Single, centralized mapping from any exception raised inside a
    resource method to backbone's error contract — the same
    ErrorResponseBuilder.from_exception(...) that used to be copy-pasted
    into every `get`/`post`/`put`/`patch`/`delete` method below (11 identical
    try/except blocks). flask-restx routes every exception a resource method
    raises through the handler registered here instead, so this is the one
    and only place that decides how errors look — exactly the point of
    having a shared response builder in the first place. Command/query
    handlers raise typed backbone exceptions (ValidationException,
    ResourceNotFoundException, ...); from_exception already knows how to
    read those, and falls back to a safe generic 500 for anything else."""

    @api.errorhandler
    def _handle_any_exception(exc: Exception):
        err = ErrorResponseBuilder.from_exception(exc)
        return err, err["status_code"]


def _register_product_routes(
    api: Api,
    create_cmd: CreateProductCommandHandler,
    update_cmd: UpdateProductCommandHandler,
    delete_cmd: DeleteProductCommandHandler,
    status_cmd: ChangeProductStatusCommandHandler,
    list_qry: GetProductsQueryHandler,
    page_qry: GetProductsPageQueryHandler,
    detail_qry: GetProductByIdQueryHandler,
) -> None:
    ns = api.namespace("api/v1/products", description="Products CRUD (PostgreSQL)")

    create_model = ns.model("CreateProduct", {
        "name":        fields.String(required=True, description="Product name (min 2 chars)"),
        "price":       fields.Float(required=True, description="Price > 0"),
        "category":    fields.String(required=True, description="Category"),
        "description": fields.String(description="Optional description"),
        "stock":       fields.Integer(description="Initial stock (default 0)"),
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
            "page":      {"description": "Page number, offset mode only (default 1)", "type": "integer"},
            "page_size": {"description": "Items per page (default 10)", "type": "integer"},
            "sort_by":   {"description": "Sort field and dir, e.g. price:desc", "type": "string"},
            "cursor":    {"description": "Opaque token from a previous response's page.next_cursor — switches to keyset pagination (ignores page)", "type": "string"},
        })
        def get(self):
            """List products. Offset-paginated by default (page/page_size);
            pass ?cursor=<token> instead to switch to keyset pagination —
            recommended for deep paging, since it doesn't degrade as the
            offset grows. The two modes are mutually exclusive: cursor,
            when present, wins."""
            if "cursor" in request.args:
                return self._get_by_cursor()
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

        def _get_by_cursor(self):
            """Keyset path: no total_count/page (a keyset window can't
            produce a total without an extra COUNT query, which would
            defeat the point) — just the page and, if there's more, a
            cursor for the next one."""
            query = GetProductsPageQuery(
                filters=request.args.getlist("filters"),
                sort_by=request.args.get("sort_by"),
                cursor=request.args.get("cursor") or None,
                page_size=int(request.args.get("page_size", 10)),
            )
            result = page_qry.handle(query)
            return CursorPaginatedResponseBuilder.success(
                items=result.items,
                next_cursor=result.next_cursor,
                message="Products retrieved successfully",
            ), 200

        @ns.expect(create_model)
        @ns.doc("create_product")
        def post(self):
            """Create a new product."""
            data = request.get_json() or {}
            cmd = CreateProductCommand(
                name=data.get("name", ""),
                price=data.get("price", 0),
                category=data.get("category", ""),
                description=data.get("description"),
                stock=data.get("stock", 0),
            )
            product_id = create_cmd.handle(cmd)
            return ProcessResponseBuilder.created(product_id), 201

    # ── /api/v1/products/<id>  (GET detail + PUT update + DELETE) ────────────
    @ns.route("/<string:product_id>")
    @ns.param("product_id", "Product UUID")
    class ProductItem(Resource):
        @ns.doc("get_product")
        def get(self, product_id: str):
            """Get a single product by ID."""
            data = detail_qry.handle(GetProductByIdQuery(product_id=product_id))
            return SimpleObjectResponseBuilder.found(data), 200

        @ns.expect(update_model)
        @ns.doc("update_product")
        def put(self, product_id: str):
            """Update an existing product (partial update supported)."""
            data = request.get_json() or {}
            cmd = UpdateProductCommand(product_id=product_id, **{
                k: data[k] for k in ("name", "price", "category", "description")
                if k in data
            })
            pid = update_cmd.handle(cmd)
            return ProcessResponseBuilder.updated(pid), 200

        @ns.doc("delete_product")
        def delete(self, product_id: str):
            """Delete a product."""
            pid = delete_cmd.handle(DeleteProductCommand(product_id=product_id))
            return ProcessResponseBuilder.deleted(pid), 200

    # ── /api/v1/products/<id>/status  (PATCH) ────────────────────────────────
    @ns.route("/<string:product_id>/status")
    @ns.param("product_id", "Product UUID")
    class ProductStatus(Resource):
        @ns.expect(status_model)
        @ns.doc("change_product_status")
        def patch(self, product_id: str):
            """Change product status (active | inactive | discontinued)."""
            data = request.get_json() or {}
            cmd = ChangeProductStatusCommand(
                product_id=product_id,
                status=data.get("status", ""),
            )
            pid = status_cmd.handle(cmd)
            return ProcessResponseBuilder.updated(pid), 200


def _register_sale_routes(
    api: Api, register_cmd: RegisterSaleCommandHandler, list_qry: GetSalesQueryHandler,
) -> None:
    ns = api.namespace("api/v1/sales", description="Sales log (MongoDB) — decrements PostgreSQL stock")

    sale_model = ns.model("RegisterSale", {
        "product_id": fields.String(required=True),
        "quantity":   fields.Integer(required=True, description="Units sold, > 0"),
    })

    @ns.route("")
    class SaleCollection(Resource):
        @ns.doc("list_sales", params={
            "product_id": {"description": "Filter by product", "type": "string"},
            "page":       {"description": "Page number (default 1)", "type": "integer"},
            "page_size":  {"description": "Items per page (default 10)", "type": "integer"},
        })
        def get(self):
            """List sales, optionally filtered by product_id."""
            query = GetSalesQuery(
                product_id=request.args.get("product_id"),
                page=int(request.args.get("page", 1)),
                page_size=int(request.args.get("page_size", 10)),
            )
            result = list_qry.handle(query)
            return PaginatedResponseBuilder.success(
                items=result.items, total_count=result.total_count,
                page=result.page, page_size=result.page_size,
                message="Sales retrieved successfully",
            ), 200

        @ns.expect(sale_model)
        @ns.doc("register_sale")
        def post(self):
            """Register a sale — decrements stock (Postgres) + logs the sale (Mongo)."""
            data = request.get_json() or {}
            cmd = RegisterSaleCommand(
                product_id=data.get("product_id", ""),
                quantity=data.get("quantity", 0),
            )
            sale_id = register_cmd.handle(cmd)
            return ProcessResponseBuilder.created(sale_id), 201


def _register_stock_movement_routes(
    api: Api, register_cmd: RegisterStockMovementCommandHandler, list_qry: GetStockMovementsQueryHandler,
) -> None:
    ns = api.namespace("api/v1/stock-movements", description="Stock movements log (MongoDB) — adjusts PostgreSQL stock")

    movement_model = ns.model("RegisterStockMovement", {
        "product_id": fields.String(required=True),
        "type":       fields.String(required=True, description="IN | OUT | ADJUSTMENT"),
        "quantity":   fields.Integer(required=True),
        "reason":     fields.String(description="Optional note"),
    })

    @ns.route("")
    class StockMovementCollection(Resource):
        @ns.doc("list_stock_movements", params={
            "product_id": {"description": "Filter by product", "type": "string"},
            "page":       {"description": "Page number (default 1)", "type": "integer"},
            "page_size":  {"description": "Items per page (default 10)", "type": "integer"},
        })
        def get(self):
            """List stock movements, optionally filtered by product_id."""
            query = GetStockMovementsQuery(
                product_id=request.args.get("product_id"),
                page=int(request.args.get("page", 1)),
                page_size=int(request.args.get("page_size", 10)),
            )
            result = list_qry.handle(query)
            return PaginatedResponseBuilder.success(
                items=result.items, total_count=result.total_count,
                page=result.page, page_size=result.page_size,
                message="Stock movements retrieved successfully",
            ), 200

        @ns.expect(movement_model)
        @ns.doc("register_stock_movement")
        def post(self):
            """Register a stock movement — adjusts stock (Postgres) + logs the movement (Mongo)."""
            data = request.get_json() or {}
            cmd = RegisterStockMovementCommand(
                product_id=data.get("product_id", ""),
                type=data.get("type", ""),
                quantity=data.get("quantity", 0),
                reason=data.get("reason"),
            )
            movement_id = register_cmd.handle(cmd)
            return ProcessResponseBuilder.created(movement_id), 201
