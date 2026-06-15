from flask import request
from flask_restx import Namespace, Resource, fields

from backbone.interfaces.response_builders import ProcessResponseBuilder, ErrorResponseBuilder

from application.commands.create_product import CreateProductCommand, CreateProductCommandHandler

ns = Namespace("products", description="Product operations")

create_model = ns.model("CreateProduct", {
    "name":        fields.String(required=True),
    "price":       fields.Float(required=True),
    "category":    fields.String(required=True),
    "description": fields.String,
})


def register(namespace: Namespace, handler: CreateProductCommandHandler) -> None:
    @namespace.route("")
    class ProductCreate(Resource):
        @namespace.expect(create_model)
        @namespace.doc("create_product")
        def post(self):
            data = request.get_json() or {}
            try:
                cmd = CreateProductCommand(
                    name=data.get("name", ""),
                    price=data.get("price", 0),
                    category=data.get("category", ""),
                    description=data.get("description"),
                )
                product_id = handler.handle(cmd)
                return ProcessResponseBuilder.created(product_id), 201
            except Exception as exc:
                err = ErrorResponseBuilder.from_exception(exc)
                return err, err["status_code"]
