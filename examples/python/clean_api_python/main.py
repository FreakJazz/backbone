"""
Clean API Python — backbone Clean Architecture + CQRS example, backed by
real databases: PostgreSQL for the product catalog (consistency-critical
stock) and MongoDB for sales/stock-movement transaction logs (append-only,
schema-light).

Setup:
    docker compose -f ../docker-compose.yml up -d
    cp .env.example .env
    python -m venv .venv
    .venv/Scripts/activate   # (or: source .venv/bin/activate on Linux/macOS)
    pip install -r requirements.txt
    python main.py

`backbone` is installed for real from GitHub via pip (see requirements.txt)
— no sys.path/sys.modules shim needed to make `from backbone.xxx import`
resolve.

Endpoints:
    GET    /api/v1/products
    GET    /api/v1/products/<id>
    POST   /api/v1/products
    PUT    /api/v1/products/<id>
    DELETE /api/v1/products/<id>
    PATCH  /api/v1/products/<id>/status
    POST   /api/v1/sales                    — decrements stock (Postgres) + logs sale (Mongo)
    GET    /api/v1/sales?product_id=...
    POST   /api/v1/stock-movements          — adjusts stock (Postgres) + logs movement (Mongo)
    GET    /api/v1/stock-movements?product_id=...
    GET    /docs  → Swagger UI
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
from flask import Flask
from flask_restx import Api

load_dotenv()

# ── Infrastructure ────────────────────────────────────────────────────────────
from infrastructure.database.postgres import create_pool, migrate
from infrastructure.database.mongodb import create_client, ensure_indexes
from infrastructure.repositories.postgres_product_repository import PostgresProductRepository
from infrastructure.repositories.mongo_sale_repository import MongoSaleRepository
from infrastructure.repositories.mongo_stock_movement_repository import MongoStockMovementRepository
from infrastructure.seeders.product_seeder import ProductSeeder

# ── Commands (write side) ─────────────────────────────────────────────────────
from application.commands.create_product import CreateProductCommandHandler
from application.commands.update_product import UpdateProductCommandHandler
from application.commands.delete_product import DeleteProductCommandHandler
from application.commands.change_product_status import ChangeProductStatusCommandHandler
from application.commands.register_sale import RegisterSaleCommandHandler
from application.commands.register_stock_movement import RegisterStockMovementCommandHandler

# ── Queries (read side) ───────────────────────────────────────────────────────
from application.queries.get_products import GetProductsQueryHandler
from application.queries.get_products_page import GetProductsPageQueryHandler
from application.queries.get_product_by_id import GetProductByIdQueryHandler
from application.queries.get_sales import GetSalesQueryHandler
from application.queries.get_stock_movements import GetStockMovementsQueryHandler

# ── Routes ────────────────────────────────────────────────────────────────────
from interfaces.http.v1.routes import register_routes


def create_app() -> Flask:
    app = Flask(__name__)

    postgres_dsn = os.environ.get("POSTGRES_DSN", "postgresql://backbone:backbone@localhost:5433/backbone_products")
    mongo_uri = os.environ.get("MONGO_URI", "mongodb://backbone:backbone@localhost:27018")
    mongo_db_name = os.environ.get("MONGO_DB", "backbone_transactions")

    # 1. PostgreSQL — product catalog
    pg_pool = create_pool(postgres_dsn)
    migrate(pg_pool)

    # 2. MongoDB — sales & stock-movement transaction logs
    mongo_client = create_client(mongo_uri)
    mongo_db = mongo_client[mongo_db_name]
    ensure_indexes(mongo_db)

    # 3. Repositories
    product_repo = PostgresProductRepository(pg_pool)
    sale_repo = MongoSaleRepository(mongo_db)
    movement_repo = MongoStockMovementRepository(mongo_db)

    ProductSeeder(product_repo).run()

    # 4. Commands
    create_cmd = CreateProductCommandHandler(product_repo)
    update_cmd = UpdateProductCommandHandler(product_repo)
    delete_cmd = DeleteProductCommandHandler(product_repo)
    status_cmd = ChangeProductStatusCommandHandler(product_repo)
    sale_cmd = RegisterSaleCommandHandler(product_repo, sale_repo)
    movement_cmd = RegisterStockMovementCommandHandler(product_repo, movement_repo)

    # 5. Queries
    list_qry = GetProductsQueryHandler(product_repo)
    page_qry = GetProductsPageQueryHandler(product_repo)
    detail_qry = GetProductByIdQueryHandler(product_repo)
    sales_qry = GetSalesQueryHandler(sale_repo)
    movements_qry = GetStockMovementsQueryHandler(movement_repo)

    # 6. API + Swagger
    api = Api(
        app,
        version="1.0",
        title="Clean API Python",
        description="backbone — Clean Architecture + CQRS example with real PostgreSQL + MongoDB",
        doc="/docs",
    )

    # 7. Routes
    register_routes(
        api, create_cmd, update_cmd, delete_cmd, status_cmd, list_qry, page_qry, detail_qry,
        sale_cmd, sales_qry, movement_cmd, movements_qry,
    )

    return app


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    # Hardcoding debug=True is a real anti-pattern, not just a style nit: the
    # Werkzeug debugger it enables lets a remote client execute arbitrary
    # Python via the traceback page if this ever gets exposed off localhost,
    # and it adds per-request overhead (reloader stat-checks, verbose
    # tracebacks) that has nothing to do with backbone or the app itself.
    debug = os.environ.get("FLASK_DEBUG", "false").lower() in ("1", "true", "yes")
    create_app().run(host="0.0.0.0", port=port, debug=debug, use_reloader=False)
