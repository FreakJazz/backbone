from domain.entities.product import Product
from domain.repositories.product_repository import IProductRepository


class ProductSeeder:
    def __init__(self, repo: IProductRepository) -> None:
        self._repo = repo

    def run(self) -> None:
        seeds = [
            Product(name="Laptop Pro", price=1500.0, category="Electronics",
                    description="High-performance laptop"),
            Product(name="Wireless Mouse", price=29.99, category="Electronics",
                    description="Ergonomic wireless mouse"),
            Product(name="Standing Desk", price=450.0, category="Furniture",
                    description="Adjustable standing desk"),
            Product(name="Coffee Mug", price=12.5, category="Kitchen",
                    description="Insulated coffee mug"),
            Product(name="Monitor 4K", price=699.0, category="Electronics",
                    description="4K UHD monitor 27 inch", status="active"),
            Product(name="Headphones BT", price=199.99, category="Electronics",
                    description="Noise-cancelling bluetooth headphones"),
            Product(name="Keyboard Mech", price=89.0, category="Electronics",
                    description="Mechanical keyboard TKL"),
            Product(name="Desk Chair", price=320.0, category="Furniture",
                    description="Ergonomic office chair"),
            Product(name="Webcam HD", price=75.0, category="Electronics",
                    description="1080p HD webcam", status="inactive"),
            Product(name="USB Hub", price=35.0, category="Electronics",
                    description="7-port USB 3.0 hub"),
        ]
        for product in seeds:
            self._repo.save(product)
