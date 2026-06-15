from backbone.domain.specifications import FilterParser, SortDirection


def parse_product_filters(raw_filters: list) -> list:
    """Convierte query params a especificaciones de filtro."""
    if not raw_filters:
        return []
    return FilterParser().parse_filters(raw_filters)


VALID_SORT_FIELDS = {"name", "price", "category", "status"}


def parse_product_sort(sort_by: str) -> tuple:
    """Parsea 'field:asc|desc'. Retorna (field, direction)."""
    if not sort_by or ":" not in sort_by:
        return "name", SortDirection.ASC
    field, direction = sort_by.split(":", 1)
    if field not in VALID_SORT_FIELDS:
        field = "name"
    dir_enum = SortDirection.DESC if direction.lower() == "desc" else SortDirection.ASC
    return field, dir_enum
