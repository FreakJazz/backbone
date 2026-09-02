from domain.entities.product import Product
from domain.repositories.product_repository import IProductRepository

_SEEDS = [
    ("Laptop Pro", "Electronics", "High-performance laptop", "active", 1500.0, 25),
    ("Wireless Mouse", "Electronics", "Ergonomic wireless mouse", "active", 29.99, 200),
    ("Standing Desk", "Furniture", "Adjustable standing desk", "active", 450.0, 15),
    ("Coffee Mug", "Kitchen", "Insulated coffee mug", "active", 12.5, 500),
    ("Monitor 4K", "Electronics", "4K UHD monitor 27 inch", "active", 699.0, 40),
    ("Headphones BT", "Electronics", "Noise-cancelling bluetooth headphones", "active", 199.99, 60),
    ("Keyboard Mech", "Electronics", "Mechanical keyboard TKL", "active", 89.0, 80),
    ("Desk Chair", "Furniture", "Ergonomic office chair", "active", 320.0, 20),
    ("Webcam HD", "Electronics", "1080p HD webcam", "inactive", 75.0, 0),
    ("USB Hub", "Electronics", "7-port USB 3.0 hub", "active", 35.0, 150),
]


class ProductSeeder:
    """Seeds a handful of products, skipping any name that already exists —
    backed by a real database that persists across restarts, re-running
    main.py must not try to insert the same name twice (it would trip the
    unique index on lower(name))."""

    def __init__(self, repo: IProductRepository) -> None:
        self._repo = repo

    def run(self) -> None:
        for name, category, description, status, price, stock in _SEEDS:
            if self._repo.find_by_name(name) is not None:
                continue
            product = Product(name=name, price=price, category=category, description=description, stock=stock)
            product.status = status
            self._repo.save(product)
