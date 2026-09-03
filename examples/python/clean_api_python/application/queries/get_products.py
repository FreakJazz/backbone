from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from backbone.infrastructure.logging import LoggerFactory

from domain.repositories.product_repository import IProductRepository
from domain.specifications.product_specs import parse_product_filters, parse_product_sort


@dataclass
class GetProductsQuery:
    filters: List[str] = field(default_factory=list)
    sort_by: Optional[str] = None
    page: int = 1
    page_size: int = 10


@dataclass
class GetProductsResult:
    items: List[Dict[str, Any]]
    total_count: int
    page: int
    page_size: int


class GetProductsQueryHandler:
    def __init__(self, repo: IProductRepository) -> None:
        self._repo = repo
        self._logger = LoggerFactory.create_for_layer(
            service_name="clean-api-python", layer="application", component="GetProductsQueryHandler",
        )

    def handle(self, query: GetProductsQuery) -> GetProductsResult:
        spec = parse_product_filters(query.filters)
        sort_field, sort_dir = parse_product_sort(query.sort_by)

        products, total = self._repo.find_all(
            spec=spec,
            sort_field=sort_field,
            sort_desc=(sort_dir == "desc"),
            page=query.page,
            page_size=query.page_size,
        )
        self._logger.info(
            "Products listed",
            context={"filters": query.filters, "total": total, "page": query.page, "page_size": query.page_size},
        )
        return GetProductsResult(
            items=[p.to_dict() for p in products],
            total_count=total,
            page=query.page,
            page_size=query.page_size,
        )
