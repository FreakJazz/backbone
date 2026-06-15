from flask_restx import Api

from application.commands.create_product import CreateProductCommandHandler
from application.commands.update_product import UpdateProductCommandHandler
from application.commands.delete_product import DeleteProductCommandHandler
from application.commands.change_product_status import ChangeProductStatusCommandHandler
from application.queries.get_products import GetProductsQueryHandler
from application.queries.get_product_by_id import GetProductByIdQueryHandler

import interfaces.http.commands.create_product_handler as create_h
import interfaces.http.commands.update_product_handler as update_h
import interfaces.http.commands.delete_product_handler as delete_h
import interfaces.http.commands.change_product_status_handler as status_h
import interfaces.http.queries.get_products_handler as list_h
import interfaces.http.queries.get_product_by_id_handler as detail_h


def register_routes(
    api: Api,
    create_cmd: CreateProductCommandHandler,
    update_cmd: UpdateProductCommandHandler,
    delete_cmd: DeleteProductCommandHandler,
    status_cmd: ChangeProductStatusCommandHandler,
    list_qry: GetProductsQueryHandler,
    detail_qry: GetProductByIdQueryHandler,
) -> None:
    ns = api.namespace("api/v1/products", description="Products")

    create_h.register(ns, create_cmd)
    update_h.register(ns, update_cmd)
    delete_h.register(ns, delete_cmd)
    status_h.register(ns, status_cmd)
    list_h.register(ns, list_qry)
    detail_h.register(ns, detail_qry)
