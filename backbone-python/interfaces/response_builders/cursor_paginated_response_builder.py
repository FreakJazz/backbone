"""
Cursor Paginated Response Builder - Respuestas paginadas por keyset/cursor

Use this instead of PaginatedResponseBuilder when the caller queried by
cursor (domain.specifications.encode_cursor/decode_cursor) rather than
page/page_size: a keyset window has no meaningful "page number", and a real
total_count would need a separate COUNT query that defeats the point of
avoiding OFFSET in the first place. This only reports what a keyset query
already produces for free — whether there's more, and the token to fetch it.
"""
from typing import Any, Dict, List, Optional


class CursorPaginatedResponseBuilder:
    """
    Constructor para respuestas paginadas por cursor.

    Contrato:
    {
        "meta": {"status": "success", "status_code": 200, "message": "..."},
        "items": [{}, {}],
        "page": {"next_cursor": "opaque-token", "has_more": true}
    }
    """

    @staticmethod
    def success(
        items: List[Any],
        next_cursor: Optional[str] = None,
        message: str = "Items retrieved successfully",
        status_code: int = 200,
    ) -> Dict[str, Any]:
        return {
            "meta": {
                "status": "success",
                "status_code": status_code,
                "message": message,
            },
            "items": items,
            "page": {
                "next_cursor": next_cursor,
                "has_more": bool(next_cursor),
            },
        }
