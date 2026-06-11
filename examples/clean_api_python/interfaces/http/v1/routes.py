"""
HTTP v1 routes — Interfaces / HTTP / v1

Single responsibility: register /api/v1 endpoints on a Flask-RESTX Api.
Receives the 6 individual HTTP handlers and wires them to URLs.
"""
from flask_restx import Api, Resource, fields, Namespace

from examples.clean_api_python.interfaces.http.commands.create_product_handler        import CreateProductHttpHandler
from examples.clean_api_python.interfaces.http.commands.update_product_handler        import UpdateProductHttpHandler
from examples.clean_api_python.interfaces.http.commands.delete_product_handler        import DeleteProductHttpHandler
from examples.clean_api_python.interfaces.http.commands.change_product_status_handler import ChangeProductStatusHttpHandler
from examples.clean_api_python.interfaces.http.queries.get_products_handler           import GetProductsHttpHandler
from examples.clean_api_python.interfaces.http.queries.get_product_by_id_handler      import GetProductByIDHttpHandler


def register_routes(
    api: Api,
    create_handler:  CreateProductHttpHandler,
    update_handler:  UpdateProductHttpHandler,
    delete_handler:  DeleteProductHttpHandler,
    status_handler:  ChangeProductStatusHttpHandler,
    list_handler:    GetProductsHttpHandler,
    get_by_id_handler: GetProductByIDHttpHandler,
) -> None:
    """Attach all v1 product routes to the Flask-RESTX Api."""

    # -------------------------------------------------------------------------
    # Swagger models
    # -------------------------------------------------------------------------
    create_model = api.model("CreateProduct", {
        "name":        fields.String(required=True,  example="Laptop Dell XPS 15"),
        "description": fields.String(example="High performance laptop"),
        "price":       fields.Float(required=True,   example=1500.00),
        "category":    fields.String(required=True,  example="Electronics"),
        "stock":       fields.Integer(required=True, example=50),
    })
    update_model = api.model("UpdateProduct", {
        "name":        fields.String(example="Laptop Updated"),
        "description": fields.String(example="New description"),
        "price":       fields.Float(example=1400.00),
        "category":    fields.String(example="Electronics"),
        "stock":       fields.Integer(example=45),
    })
    status_model = api.model("ChangeStatus", {
        "active": fields.Boolean(required=True, example=False),
    })
    id_model = api.model("IDResponse", {
        "id": fields.String(description="Resource ID"),
    })
    meta_model = api.model("Meta", {
        "status":      fields.String(),
        "status_code": fields.Integer(),
        "message":     fields.String(),
    })
    pagination_model = api.model("Pagination", {
        "total_count": fields.Integer(),
        "page":        fields.Integer(),
        "page_size":   fields.Integer(),
    })
    paginated_model = api.model("PaginatedProducts", {
        "meta":       fields.Nested(meta_model),
        "items":      fields.List(fields.Raw()),
        "pagination": fields.Nested(pagination_model),
    })
    error_model = api.model("ErrorResponse", {
        "request_id":  fields.String(),
        "status_code": fields.Integer(),
        "message":     fields.String(),
        "code_error":  fields.String(),
        "field_errors": fields.Raw(),
    })

    # -------------------------------------------------------------------------
    # Namespace
    # -------------------------------------------------------------------------
    ns = Namespace("products", description="Product operations", path="/v1/products")
    api.add_namespace(ns)

    # -------------------------------------------------------------------------
    # Collection  GET + POST
    # -------------------------------------------------------------------------
    @ns.route("")
    class ProductCollection(Resource):

        @ns.doc("list_products", params={
            "filters":   "Repeated. Format: field,operator,value[,condition]. "
                         "Operators: eq ne gt gte lt lte contains in between is_null is_not_null. "
                         "Example: ?filters=category,eq,Electronics,and&filters=price,gt,500",
            "page":      "Page number (default 1)",
            "page_size": "Items per page (default 10)",
            "sort_by":   "field:direction — e.g. price:desc (default created_at:desc)",
        })
        @ns.response(200, "OK", paginated_model)
        @ns.response(500, "Server error", error_model)
        def get(self):
            """List products with dynamic filters (CQRS query)."""
            response, status = list_handler.handle()
            return response.get_json(), status

        @ns.doc("create_product")
        @ns.expect(create_model)
        @ns.response(201, "Created", id_model)
        @ns.response(400, "Validation error", error_model)
        def post(self):
            """Create a new product (CQRS command). Returns {"id": "uuid"}."""
            response, status = create_handler.handle()
            return response.get_json(), status

    # -------------------------------------------------------------------------
    # Item  GET + PUT + DELETE
    # -------------------------------------------------------------------------
    @ns.route("/<string:product_id>")
    @ns.param("product_id", "Product ID")
    class ProductItem(Resource):

        @ns.response(200, "OK")
        @ns.response(404, "Not found", error_model)
        def get(self, product_id: str):
            """Get a product by ID (CQRS query). Returns the raw object."""
            response, status = get_by_id_handler.handle(product_id)
            return response.get_json(), status

        @ns.doc("update_product")
        @ns.expect(update_model)
        @ns.response(200, "Updated", id_model)
        @ns.response(404, "Not found", error_model)
        def put(self, product_id: str):
            """Update a product (CQRS command). Returns {"id": "uuid"}."""
            response, status = update_handler.handle(product_id)
            return response.get_json(), status

        @ns.response(200, "Deleted", id_model)
        @ns.response(404, "Not found", error_model)
        def delete(self, product_id: str):
            """Delete a product (CQRS command). Returns {"id": "uuid"}."""
            response, status = delete_handler.handle(product_id)
            return response.get_json(), status

    # -------------------------------------------------------------------------
    # Status  PATCH
    # -------------------------------------------------------------------------
    @ns.route("/<string:product_id>/status")
    @ns.param("product_id", "Product ID")
    class ProductStatus(Resource):

        @ns.doc("change_status")
        @ns.expect(status_model)
        @ns.response(200, "Updated", id_model)
        @ns.response(404, "Not found", error_model)
        def patch(self, product_id: str):
            """Activate / deactivate a product (CQRS command). Returns {"id": "uuid"}."""
            response, status = status_handler.handle(product_id)
            return response.get_json(), status
