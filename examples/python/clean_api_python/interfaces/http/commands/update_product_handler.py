from flask import request
from flask_restx import Namespace, Resource, fields

from backbone.interfaces.response_builders import ProcessResponseBuilder, ErrorResponseBuilder

from application.commands.update_product import UpdateProductCommand, UpdateProductCommandHandler

update_model_fields = {
    "name":        fields.String,
    "price":       fields.Float,
    "category":    fields.String,
    "description": fields.String,
}


def register(namespace: Namespace, handler: UpdateProductCommandHandler) -> None:
    update_model = namespace.model("UpdateProduct", update_model_fields)

    @namespace.route("/<string:product_id>")
    class ProductUpdate(Resource):
        @namespace.expect(update_model)
        @namespace.doc("update_product")
        def put(self, product_id: str):
            data = request.get_json() or {}
            try:
                cmd = UpdateProductCommand(product_id=product_id, **{
                    k: data[k] for k in ("name", "price", "category", "description")
                    if k in data
                })
                pid = handler.handle(cmd)
                return ProcessResponseBuilder.updated(pid), 200
            except Exception as exc:
                err = ErrorResponseBuilder.from_exception(exc)
                return err, err["status_code"]
