from flask_restx import Namespace, Resource

from backbone.interfaces.response_builders import ProcessResponseBuilder, ErrorResponseBuilder

from application.commands.delete_product import DeleteProductCommand, DeleteProductCommandHandler


def register(namespace: Namespace, handler: DeleteProductCommandHandler) -> None:
    @namespace.route("/<string:product_id>")
    class ProductDelete(Resource):
        @namespace.doc("delete_product")
        def delete(self, product_id: str):
            try:
                pid = handler.handle(DeleteProductCommand(product_id=product_id))
                return ProcessResponseBuilder.deleted(pid), 200
            except Exception as exc:
                err = ErrorResponseBuilder.from_exception(exc)
                return err, err["status_code"]
