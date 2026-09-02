from abc import ABC, abstractmethod
from typing import List, Optional, Tuple

from ..entities.stock_movement import StockMovement


class IStockMovementRepository(ABC):
    @abstractmethod
    def save(self, movement: StockMovement) -> StockMovement: ...

    @abstractmethod
    def find_by_product_id(
        self, product_id: Optional[str], page: int = 1, page_size: int = 10
    ) -> Tuple[List[StockMovement], int]: ...
