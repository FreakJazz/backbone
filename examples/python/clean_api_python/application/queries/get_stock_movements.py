from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from backbone.infrastructure.logging import LoggerFactory

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
        self._logger = LoggerFactory.create_for_layer(
            service_name="clean-api-python", layer="application", component="GetStockMovementsQueryHandler",
        )

    def handle(self, query: GetStockMovementsQuery) -> GetStockMovementsResult:
        movements, total = self._repo.find_by_product_id(query.product_id, query.page, query.page_size)
        self._logger.info(
            "Stock movements listed",
            context={"product_id": query.product_id, "total": total, "page": query.page},
        )
        return GetStockMovementsResult(
            items=[m.to_dict() for m in movements],
            total_count=total,
            page=query.page,
            page_size=query.page_size,
        )
