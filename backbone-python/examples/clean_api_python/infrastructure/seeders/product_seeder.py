"""Product seeder — Infrastructure / Seeders"""
from datetime import datetime
import sys, os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../..')))

from backbone.infrastructure.logging import LoggerFactory
from examples.clean_api_python.domain.entities.product import Product
from examples.clean_api_python.domain.repositories.product_repository import ProductRepository

_SEED_PRODUCTS = [
    {"id": "1", "name": "Laptop Dell XPS 15",    "description": "High performance laptop with 16GB RAM", "price": 1500.00, "category": "Electronics", "stock": 50},
    {"id": "2", "name": "iPhone 14 Pro",          "description": "Latest iPhone with advanced camera",    "price": 1200.00, "category": "Electronics", "stock": 100},
    {"id": "3", "name": "Office Chair Ergonomic", "description": "Comfortable ergonomic office chair",    "price": 350.00,  "category": "Furniture",   "stock": 30},
    {"id": "4", "name": "Standing Desk",          "description": "Adjustable height standing desk",       "price": 600.00,  "category": "Furniture",   "stock": 20},
    {"id": "5", "name": "Wireless Mouse",         "description": "Ergonomic wireless mouse",              "price": 45.00,   "category": "Electronics", "stock": 200},
]


class ProductSeeder:

    def __init__(self, repository: ProductRepository):
        self.repository = repository
        self.logger = LoggerFactory.create_layer_logger(
            "product-api", "infrastructure", "ProductSeeder"
        )

    def run(self) -> None:
        self.logger.info("Running product seeder...")
        now = datetime.now()
        seeded = 0

        for data in _SEED_PRODUCTS:
            try:
                product = Product(
                    id=data["id"],
                    name=data["name"],
                    description=data["description"],
                    price=data["price"],
                    category=data["category"],
                    stock=data["stock"],
                    created_at=now,
                    updated_at=now,
                )
                self.repository.create(product)
                seeded += 1
            except Exception as e:
                self.logger.warning("Failed to seed product", extra_data={
                    "product_id": data["id"], "error": str(e),
                })

        self.logger.info("Product seeder completed", extra_data={"seeded": seeded})
