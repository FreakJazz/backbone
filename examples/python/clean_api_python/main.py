"""
Clean API Python — ejemplo de Clean Architecture + CQRS con backbone.

Setup:
    pip install -e ../../backbone-python
    pip install flask flask-restx
    python main.py

Endpoints:
    GET    /api/v1/products
    GET    /api/v1/products/<id>
    POST   /api/v1/products
    PUT    /api/v1/products/<id>
    DELETE /api/v1/products/<id>
    PATCH  /api/v1/products/<id>/status
    GET    /docs  → Swagger UI
"""
import sys
import os
import types

_here = os.path.dirname(os.path.abspath(__file__))
_bb_root = os.path.abspath(os.path.join(_here, "..", "..", "..", "backbone-python"))

# backbone-python/ es la raíz del paquete backbone (sin subcarpeta backbone/).
# El módulo virtual 'backbone' apunta a backbone-python/ para que
# 'from backbone.xxx import' resuelva correctamente con imports relativos internos.
# IMPORTANTE: NO agregar _bb_root a sys.path directamente — causaría que Python
# mezcle backbone-python/infrastructure/ con infrastructure/ del ejemplo.
_bb = types.ModuleType("backbone")
_bb.__path__ = [_bb_root]
_bb.__package__ = "backbone"
sys.modules["backbone"] = _bb

sys.path.insert(0, _here)

from flask import Flask
from flask_restx import Api

# ── Infrastructure ────────────────────────────────────────────────────────────
from infrastructure.repositories.memory_product_repository import MemoryProductRepository
from infrastructure.seeders.product_seeder import ProductSeeder

# ── Commands (write side) ─────────────────────────────────────────────────────
from application.commands.create_product import CreateProductCommandHandler
from application.commands.update_product import UpdateProductCommandHandler
from application.commands.delete_product import DeleteProductCommandHandler
from application.commands.change_product_status import ChangeProductStatusCommandHandler

# ── Queries (read side) ───────────────────────────────────────────────────────
from application.queries.get_products import GetProductsQueryHandler
from application.queries.get_product_by_id import GetProductByIdQueryHandler

# ── Routes ────────────────────────────────────────────────────────────────────
from interfaces.http.v1.routes import register_routes


def create_app() -> Flask:
    app = Flask(__name__)

    # 1. Infrastructure
    repo = MemoryProductRepository()
    ProductSeeder(repo).run()

    # 2. Commands
    create_cmd = CreateProductCommandHandler(repo)
    update_cmd = UpdateProductCommandHandler(repo)
    delete_cmd = DeleteProductCommandHandler(repo)
    status_cmd = ChangeProductStatusCommandHandler(repo)

    # 3. Queries
    list_qry   = GetProductsQueryHandler(repo)
    detail_qry = GetProductByIdQueryHandler(repo)

    # 4. API + Swagger
    api = Api(
        app,
        version="1.0",
        title="Clean API Python",
        description="backbone — Clean Architecture + CQRS example",
        doc="/docs",
    )

    # 5. Routes
    register_routes(api, create_cmd, update_cmd, delete_cmd, status_cmd, list_qry, detail_qry)

    return app


if __name__ == "__main__":
    create_app().run(host="0.0.0.0", port=5000, debug=True)
