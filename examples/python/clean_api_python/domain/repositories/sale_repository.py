from abc import ABC, abstractmethod
from typing import List, Optional, Tuple

from ..entities.sale import Sale


class ISaleRepository(ABC):
    @abstractmethod
    def save(self, sale: Sale) -> Sale: ...

    @abstractmethod
    def find_by_product_id(
        self, product_id: Optional[str], page: int = 1, page_size: int = 10
    ) -> Tuple[List[Sale], int]: ...
