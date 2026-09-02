from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from domain.repositories.stock_movement_repository import IStockMovementRepository


@dataclass
class GetStockMovementsQuery:
    product_id: Optional[str] = None
    page: int = 1
    page_size: int = 10


@dataclass
class GetStockMovementsResult:
    items: List[Dict[str, Any]]
    total_count: int
    page: int
    page_size: int


class GetStockMovementsQueryHandler:
    def __init__(self, repo: IStockMovementRepository) -> None:
        self._repo = repo

    def handle(self, query: GetStockMovementsQuery) -> GetStockMovementsResult:
        movements, total = self._repo.find_by_product_id(query.product_id, query.page, query.page_size)
        return GetStockMovementsResult(
            items=[m.to_dict() for m in movements],
            total_count=total,
            page=query.page,
            page_size=query.page_size,
        )
