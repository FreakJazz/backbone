"""
Application entry point — DI container + server start.

main.py responsibilities (nothing else):
  1. Instantiate infrastructure (repositories)
  2. Run seeders
  3. Wire command handlers        (application / commands)
  4. Wire query handlers          (application / queries)
  5. Wire HTTP command handlers   (interfaces / http / commands)
  6. Wire HTTP query handlers     (interfaces / http / queries)
  7. Register versioned routes    (interfaces / http / v1)
  8. Start server
"""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from flask import Flask, jsonify
from flask_restx import Api

from backbone.infrastructure.logging import LoggerFactory

# ── Infrastructure ────────────────────────────────────────────────────────────
from examples.clean_api_python.infrastructure.repositories.memory_product_repository import MemoryProductRepository
from examples.clean_api_python.infrastructure.seeders.product_seeder import ProductSeeder

# ── Application commands (write side) ────────────────────────────────────────
from examples.clean_api_python.application.commands.create_product        import CreateProductCommandHandler
from examples.clean_api_python.application.commands.update_product        import UpdateProductCommandHandler
from examples.clean_api_python.application.commands.delete_product        import DeleteProductCommandHandler
from examples.clean_api_python.application.commands.change_product_status import ChangeProductStatusCommandHandler

# ── Application queries (read side) ──────────────────────────────────────────
from examples.clean_api_python.application.queries.get_products      import GetProductsQueryHandler
from examples.clean_api_python.application.queries.get_product_by_id import GetProductByIDQueryHandler

# ── HTTP command handlers (interfaces / commands) ─────────────────────────────
from examples.clean_api_python.interfaces.http.commands.create_product_handler        import CreateProductHttpHandler
from examples.clean_api_python.interfaces.http.commands.update_product_handler        import UpdateProductHttpHandler
from examples.clean_api_python.interfaces.http.commands.delete_product_handler        import DeleteProductHttpHandler
from examples.clean_api_python.interfaces.http.commands.change_product_status_handler import ChangeProductStatusHttpHandler

# ── HTTP query handlers (interfaces / queries) ────────────────────────────────
from examples.clean_api_python.interfaces.http.queries.get_products_handler      import GetProductsHttpHandler
from examples.clean_api_python.interfaces.http.queries.get_product_by_id_handler import GetProductByIDHttpHandler

# ── Versioned routes ──────────────────────────────────────────────────────────
from examples.clean_api_python.interfaces.http.v1.routes import register_routes


def create_app() -> Flask:
    app = Flask(__name__)
    app.config["RESTX_MASK_SWAGGER"] = False

    api = Api(
        app,
        version="1.0",
        title="Product API",
        description="Clean Architecture + CQRS — backbone Python",
        doc="/docs",
        prefix="/api",
    )

    logger = LoggerFactory.create_logger("product-api")
    logger.info("Initializing application", extra_data={"version": "1.0.0"})

    # 1. Infrastructure
    product_repo = MemoryProductRepository()

    # 2. Seeders
    ProductSeeder(product_repo).run()

    # 3. Application command handlers
    create_cmd  = CreateProductCommandHandler(product_repo)
    update_cmd  = UpdateProductCommandHandler(product_repo)
    delete_cmd  = DeleteProductCommandHandler(product_repo)
    status_cmd  = ChangeProductStatusCommandHandler(product_repo)

    # 4. Application query handlers
    get_list_qry  = GetProductsQueryHandler(product_repo)
    get_by_id_qry = GetProductByIDQueryHandler(product_repo)

    # 5. HTTP command handlers  (one per operation)
    create_http  = CreateProductHttpHandler(create_cmd)
    update_http  = UpdateProductHttpHandler(update_cmd)
    delete_http  = DeleteProductHttpHandler(delete_cmd)
    status_http  = ChangeProductStatusHttpHandler(status_cmd)

    # 6. HTTP query handlers  (one per operation)
    list_http      = GetProductsHttpHandler(get_list_qry)
    get_by_id_http = GetProductByIDHttpHandler(get_by_id_qry)

    # 7. Routes
    register_routes(
        api,
        create_handler=create_http,
        update_handler=update_http,
        delete_handler=delete_http,
        status_handler=status_http,
        list_handler=list_http,
        get_by_id_handler=get_by_id_http,
    )

    @app.route("/health", methods=["GET"])
    def health():
        return jsonify({"status": "healthy", "service": "product-api"}), 200

    logger.info("Application ready", extra_data={"docs": "/docs"})
    return app


if __name__ == "__main__":
    app = create_app()

    print("\nServer  → http://localhost:5000")
    print("Swagger → http://localhost:5000/docs")
    print("\nEndpoints (v1):")
    print("  POST   /api/v1/products")
    print("  GET    /api/v1/products?filters=category,eq,Electronics,and&page=1&page_size=10&sort_by=price:desc")
    print("  GET    /api/v1/products/<id>")
    print("  PUT    /api/v1/products/<id>")
    print("  DELETE /api/v1/products/<id>")
    print("  PATCH  /api/v1/products/<id>/status")
    print("  GET    /health")
    print("\nPress Ctrl+C to stop\n")

    host = os.getenv("HOST", "127.0.0.1")
    port = int(os.getenv("PORT", "5000"))
    app.run(debug=True, host=host, port=port)
