from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from domain.repositories.sale_repository import ISaleRepository


@dataclass
class GetSalesQuery:
    product_id: Optional[str] = None
    page: int = 1
    page_size: int = 10


@dataclass
class GetSalesResult:
    items: List[Dict[str, Any]]
    total_count: int
    page: int
    page_size: int


class GetSalesQueryHandler:
    def __init__(self, repo: ISaleRepository) -> None:
        self._repo = repo

    def handle(self, query: GetSalesQuery) -> GetSalesResult:
        sales, total = self._repo.find_by_product_id(query.product_id, query.page, query.page_size)
        return GetSalesResult(
            items=[s.to_dict() for s in sales],
            total_count=total,
            page=query.page,
            page_size=query.page_size,
        )
