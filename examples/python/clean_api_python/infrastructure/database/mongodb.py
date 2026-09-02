"""MongoDB client + index bootstrap for the sales / stock-movement logs."""
from pymongo import ASCENDING, DESCENDING, MongoClient
from pymongo.database import Database


def create_client(uri: str) -> MongoClient:
    client = MongoClient(uri, serverSelectionTimeoutMS=5000)
    client.admin.command("ping")  # fail fast if unreachable
    return client


def ensure_indexes(db: Database) -> None:
    """Both collections are queried almost exclusively by product_id ordered
    by recency, so a compound index on (product_id, created_at) covers that
    access pattern without a separate sort step."""
    db["sales"].create_index([("product_id", ASCENDING), ("created_at", DESCENDING)])
    db["stock_movements"].create_index([("product_id", ASCENDING), ("created_at", DESCENDING)])
