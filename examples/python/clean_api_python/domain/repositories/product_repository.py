from abc import ABC, abstractmethod
from typing import List, Optional, Tuple

from backbone.domain.specifications import Specification

from ..entities.product import Product


class InsufficientStockError(Exception):
    """Raised by adjust_stock when applying delta would take stock below
    zero. Callers translate it into a 409 Conflict."""


class IProductRepository(ABC):
    @abstractmethod
    def save(self, product: Product) -> Product: ...

    @abstractmethod
    def find_by_id(self, product_id: str) -> Optional[Product]: ...

    @abstractmethod
    def find_all(
        self,
        spec: Optional[Specification] = None,
        sort_field: str = "name",
        sort_desc: bool = False,
        page: int = 1,
        page_size: int = 10,
    ) -> Tuple[List[Product], int]: ...

    @abstractmethod
    def find_by_name(self, name: str) -> Optional[Product]: ...

    @abstractmethod
    def delete(self, product_id: str) -> None: ...

    @abstractmethod
    def exists(self, product_id: str) -> bool: ...

    @abstractmethod
    def adjust_stock(self, product_id: str, delta: int) -> int:
        """Atomically applies delta (positive or negative) to a product's
        stock. The production (Postgres) implementation does this in a
        single UPDATE ... WHERE stock + delta >= 0 statement, so two
        concurrent sales can never oversell the same unit. Raises
        InsufficientStockError instead of a generic error so callers can
        map it to 409. Returns the new stock value."""
        ...

    @abstractmethod
    def find_page_by_cursor(
        self,
        spec: Optional[Specification],
        sort_field: str,
        sort_desc: bool,
        after_cursor: Optional[str],
        limit: int,
    ) -> Tuple[List[Product], Optional[str]]:
        """Returns up to `limit` products matching spec, ordered by
        sort_field then id, starting strictly after the row identified by
        after_cursor (an opaque token from
        backbone.domain.specifications.encode_cursor — None to start from
        the beginning). Returns the page and, when there may be more rows,
        a cursor for the next page (None when this is the last page).

        Unlike find_all's page/page_size (LIMIT/OFFSET), this never
        degrades as the client pages deeper into a large result set: the
        Postgres implementation seeks directly via the (sort_field, id)
        ordering instead of scanning and discarding every skipped row,
        which is what OFFSET does no matter how large the offset gets."""
        ...
