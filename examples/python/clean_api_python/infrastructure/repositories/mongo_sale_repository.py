from typing import List, Optional, Tuple

from pymongo.database import Database

from domain.entities.sale import Sale
from domain.repositories.sale_repository import ISaleRepository


class MongoSaleRepository(ISaleRepository):
    def __init__(self, db: Database) -> None:
        self._col = db["sales"]

    def save(self, sale: Sale) -> Sale:
        self._col.insert_one(sale.to_doc())
        return sale

    def find_by_product_id(
        self, product_id: Optional[str], page: int = 1, page_size: int = 10
    ) -> Tuple[List[Sale], int]:
        """Uses a single $facet aggregation instead of count_documents()
        followed by find(): both branches run against the same $match stage
        in one round trip to Mongo — the append-only sales log only grows,
        so keeping this at one round trip is what actually matters as it
        does. Unlike the SQL COUNT(*) OVER() equivalent, the totalCount
        branch here is independent of the data branch's $skip/$limit, so it
        stays correct even when the requested page is past the last one."""
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
        return [_doc_to_sale(doc) for doc in result["data"]], total


def _doc_to_sale(doc: dict) -> Sale:
    return Sale(
        id=doc["_id"], product_id=doc["product_id"], quantity=doc["quantity"],
        unit_price=doc["unit_price"], created_at=doc["created_at"],
    )
