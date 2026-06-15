from flask import request
from flask_restx import Namespace, Resource, fields

from backbone.interfaces.response_builders import ProcessResponseBuilder, ErrorResponseBuilder

from application.commands.change_product_status import (
    ChangeProductStatusCommand, ChangeProductStatusCommandHandler,
)

status_model_fields = {"status": fields.String(required=True)}


def register(namespace: Namespace, handler: ChangeProductStatusCommandHandler) -> None:
    status_model = namespace.model("ChangeStatus", status_model_fields)

    @namespace.route("/<string:product_id>/status")
    class ProductStatus(Resource):
        @namespace.expect(status_model)
        @namespace.doc("change_product_status")
        def patch(self, product_id: str):
            data = request.get_json() or {}
            try:
                cmd = ChangeProductStatusCommand(
                    product_id=product_id,
                    status=data.get("status", ""),
                )
                pid = handler.handle(cmd)
                return ProcessResponseBuilder.updated(pid), 200
            except Exception as exc:
                err = ErrorResponseBuilder.from_exception(exc)
                return err, err["status_code"]
