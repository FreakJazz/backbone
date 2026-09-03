from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from backbone.domain.specifications import decode_cursor
from backbone.errors import ErrorCodes
from backbone.application.exceptions import ValidationException
from backbone.infrastructure.logging import LoggerFactory

from domain.repositories.product_repository import IProductRepository
from domain.specifications.product_specs import parse_product_filters, VALID_SORT_FIELDS


@dataclass
class GetProductsPageQuery:
    filters: List[str] = field(default_factory=list)
    sort_by: Optional[str] = None
    cursor: Optional[str] = None  # None starts from the beginning
    page_size: int = 10


@dataclass
class GetProductsPageResult:
    items: List[Dict[str, Any]]
    next_cursor: Optional[str]


class GetProductsPageQueryHandler:
    """Cursor ("keyset") counterpart to GetProductsQueryHandler. A separate
    handler rather than a branch inside GetProductsQueryHandler so the
    well-tested offset path stays untouched — this is purely additive."""

    def __init__(self, repo: IProductRepository) -> None:
        self._repo = repo
        self._logger = LoggerFactory.create_for_layer(
            service_name="clean-api-python", layer="application", component="GetProductsPageQueryHandler",
        )

    def handle(self, query: GetProductsPageQuery) -> GetProductsPageResult:
        # A malformed cursor is a client input error (400), not a server
        # failure (500) — validate it here, before it ever reaches the
        # repository, same as filters are validated by parse_product_filters.
        # The repository decodes it again to get the value it actually needs
        # to bind; that's a second pass over a few bytes of base64, not
        # worth threading a decoded value through the interface to save it.
        if query.cursor:
            try:
                decode_cursor(query.cursor)
            except ValueError as exc:
                self._logger.warning("Invalid cursor", context={"cursor": query.cursor, "error": str(exc)})
                raise ValidationException(str(exc), code=ErrorCodes.APP_VALIDATION_FAILURE)

        spec = parse_product_filters(query.filters)

        sort_field, sort_desc = "created_at", True
        if query.sort_by:
            field_name, direction = _split_sort_by(query.sort_by)
            if field_name in VALID_SORT_FIELDS:
                sort_field, sort_desc = field_name, direction == "desc"

        products, next_cursor = self._repo.find_page_by_cursor(
            spec, sort_field, sort_desc, query.cursor, query.page_size,
        )
        self._logger.info(
            "Products listed by cursor",
            context={"filters": query.filters, "count": len(products), "has_more": next_cursor is not None},
        )
        return GetProductsPageResult(
            items=[p.to_dict() for p in products],
            next_cursor=next_cursor,
        )


def _split_sort_by(sort_by: str) -> tuple:
    sort_by = sort_by.replace(":", ",")
    parts = sort_by.split(",", 1)
    field_name = parts[0].strip()
    direction = "desc"
    if len(parts) == 2 and parts[1].strip().lower() == "asc":
        direction = "asc"
    return field_name, direction
