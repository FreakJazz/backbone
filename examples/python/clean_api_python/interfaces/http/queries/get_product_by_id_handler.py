from flask_restx import Namespace, Resource

from backbone.interfaces.response_builders import SimpleObjectResponseBuilder, ErrorResponseBuilder

from application.queries.get_product_by_id import GetProductByIdQuery, GetProductByIdQueryHandler


def register(namespace: Namespace, handler: GetProductByIdQueryHandler) -> None:
    @namespace.route("/<string:product_id>")
    class ProductDetail(Resource):
        @namespace.doc("get_product_by_id")
        def get(self, product_id: str):
            try:
                data = handler.handle(GetProductByIdQuery(product_id=product_id))
                return SimpleObjectResponseBuilder.found(data), 200
            except Exception as exc:
                err = ErrorResponseBuilder.from_exception(exc)
                return err, err["status_code"]
