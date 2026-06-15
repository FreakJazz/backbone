from abc import ABC, abstractmethod
from typing import List, Optional, Tuple

from ..entities.product import Product


class IProductRepository(ABC):
    @abstractmethod
    def save(self, product: Product) -> Product: ...

    @abstractmethod
    def find_by_id(self, product_id: str) -> Optional[Product]: ...

    @abstractmethod
    def find_all(
        self,
        filters: Optional[list] = None,
        sort_by: Optional[str] = None,
        page: int = 1,
        page_size: int = 10,
    ) -> Tuple[List[Product], int]: ...

    @abstractmethod
    def delete(self, product_id: str) -> None: ...

    @abstractmethod
    def exists(self, product_id: str) -> bool: ...
