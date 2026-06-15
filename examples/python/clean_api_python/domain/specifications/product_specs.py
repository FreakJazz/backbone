from typing import Optional

from backbone.domain.specifications import FilterParser, Specification, SortDirection


VALID_SORT_FIELDS = {"name", "price", "category", "status"}


def parse_product_filters(raw_filters: list) -> Optional[Specification]:
    """Convierte query params a una Specification compuesta (o None si no hay filtros)."""
    if not raw_filters:
        return None
    return FilterParser().parse_filters(raw_filters)


def parse_product_sort(sort_by: Optional[str]) -> tuple:
    """Parsea 'field:asc|desc'. Retorna (field, direction_str)."""
    if not sort_by or ":" not in sort_by:
        return "name", "asc"
    field, direction = sort_by.split(":", 1)
    if field not in VALID_SORT_FIELDS:
        field = "name"
    return field, direction.lower()
