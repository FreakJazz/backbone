from typing import List, Optional, Tuple

from pymongo.database import Database

from domain.entities.stock_movement import StockMovement
from domain.repositories.stock_movement_repository import IStockMovementRepository


class MongoStockMovementRepository(IStockMovementRepository):
    def __init__(self, db: Database) -> None:
        self._col = db["stock_movements"]

    def save(self, movement: StockMovement) -> StockMovement:
        self._col.insert_one(movement.to_doc())
        return movement

    def find_by_product_id(
        self, product_id: Optional[str], page: int = 1, page_size: int = 10
    ) -> Tuple[List[StockMovement], int]:
        """Single $facet aggregation instead of count_documents() + find() —
        see MongoSaleRepository's equivalent method for the rationale."""
        page = max(page, 1)
        page_size = min(max(page_size, 1), 100)
        match = {"product_id": product_id} if product_id else {}

        pipeline = [
            {"$match": match},
            {"$sort": {"created_at": -1}},
            {"$facet": {
                "data": [
                    {"$skip": (page - 1) * page_size},
                    {"$limit": page_size},
                ],
                "totalCount": [{"$count": "count"}],
            }},
        ]
        result = next(self._col.aggregate(pipeline), None)
        if result is None:
            return [], 0

        total_count = result["totalCount"]
        total = total_count[0]["count"] if total_count else 0
        return [_doc_to_movement(doc) for doc in result["data"]], total


def _doc_to_movement(doc: dict) -> StockMovement:
    return StockMovement(
        id=doc["_id"], product_id=doc["product_id"], type=doc["type"], quantity=doc["quantity"],
        delta=doc["delta"], reason=doc.get("reason"), created_at=doc["created_at"],
    )
