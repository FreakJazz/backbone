from abc import ABC, abstractmethod
from typing import List, Optional, Tuple

from backbone.domain.specifications import Specification

from ..entities.product import Product


class IProductRepository(ABC):
    @abstractmethod
    def save(self, product: Product) -> Product: ...

    @abstractmethod
    def find_by_id(self, product_id: str) -> Optional[Product]: ...

    @abstractmethod
    def find_all(
        self,
        spec: Optional[Specification] = None,
        sort_field: str = "name",
        sort_desc: bool = False,
        page: int = 1,
        page_size: int = 10,
    ) -> Tuple[List[Product], int]: ...

    @abstractmethod
    def find_by_name(self, name: str) -> Optional[Product]: ...

    @abstractmethod
    def delete(self, product_id: str) -> None: ...

    @abstractmethod
    def exists(self, product_id: str) -> bool: ...
