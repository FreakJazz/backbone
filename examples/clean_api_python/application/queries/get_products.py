"""GetProducts query + handler — Application / Queries"""
from dataclasses import dataclass, field
from typing import List, Dict, Any
import sys, os, time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../..')))

from backbone.domain.specifications import FilterParser, SortParser
from backbone.infrastructure.logging import LoggerFactory
from examples.clean_api_python.domain.entities.product import Product
from examples.clean_api_python.domain.repositories.product_repository import ProductRepository


@dataclass
class GetProductsQuery:
    """
    Read query for listing products.

    Query params:
      filters   — repeated: "field,operator,value[,condition]"
                  operators : eq ne gt gte lt lte contains in between is_null is_not_null
                  conditions: and (default) | or
      page      — page number (default 1)
      page_size — items per page (default 10)
      sort_by   — "field:direction"  e.g. "price:desc"  (default "created_at:desc")
    """
    filters: List[str] = field(default_factory=list)
    page: int = 1
    page_size: int = 10
    sort_by: str = "created_at:desc"


@dataclass
class GetProductsResult:
    products: List[Product]
    total_count: int
    page: int
    page_size: int


class GetProductsQueryHandler:

    def __init__(self, repository: ProductRepository):
        self.repository = repository
        self.logger = LoggerFactory.create_layer_logger(
            "product-api", "application", "GetProductsQueryHandler"
        )

    def handle(self, query: GetProductsQuery, context: Dict[str, Any]) -> GetProductsResult:
        self.logger.info("Handling GetProductsQuery", extra_data={
            "filters": query.filters, "page": query.page,
            "page_size": query.page_size, "sort_by": query.sort_by,
        })

        start = time.time()

        # Parse filters → composed Specification
        spec = FilterParser().parse_filters(query.filters) if query.filters else None

        # Parse sort_by → list of (field, direction) tuples
        sort_str = query.sort_by.replace(":", ",") if query.sort_by else "created_at,desc"
        sort_spec = SortParser().parse_sort(sort_str)
        sorts = sort_spec.to_sort_criteria() if sort_spec else [("created_at", "desc")]

        total_count = self.repository.count(spec)

        products = self.repository.find_by_criteria(
            filters=spec,
            sorts=sorts,
            page=query.page,
            page_size=query.page_size,
        )

        self.logger.info("GetProductsQuery handled", extra_data={
            "count": len(products), "total": total_count,
            "duration_ms": int((time.time() - start) * 1000),
        })

        return GetProductsResult(
            products=products,
            total_count=total_count,
            page=query.page,
            page_size=query.page_size,
        )
