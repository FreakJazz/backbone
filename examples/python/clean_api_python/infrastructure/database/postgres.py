"""PostgreSQL connection pool + schema bootstrap for the product catalog."""
from psycopg_pool import ConnectionPool

DDL = """
CREATE TABLE IF NOT EXISTS products (
    id          TEXT PRIMARY KEY,
    name        TEXT NOT NULL,
    price       DOUBLE PRECISION NOT NULL CHECK (price > 0),
    category    TEXT NOT NULL,
    status      TEXT NOT NULL DEFAULT 'active',
    description TEXT NOT NULL DEFAULT '',
    stock       INTEGER NOT NULL DEFAULT 0 CHECK (stock >= 0),
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_products_category   ON products (category);
CREATE INDEX IF NOT EXISTS idx_products_status     ON products (status);
CREATE INDEX IF NOT EXISTS idx_products_created_at ON products (created_at DESC);
CREATE UNIQUE INDEX IF NOT EXISTS uq_products_name_lower ON products (lower(name));
"""


def create_pool(dsn: str) -> ConnectionPool:
    """Opens a pool and blocks until at least one connection is ready.

    min_size=2 keeps a couple of connections warm so a cold pool doesn't
    cost a TCP+TLS handshake on the first request after idle."""
    pool = ConnectionPool(conninfo=dsn, min_size=2, max_size=10, open=True)
    pool.wait(timeout=10)
    return pool


def migrate(pool: ConnectionPool) -> None:
    """Idempotent CREATE TABLE for a runnable example. A real service should
    own its schema with a versioned migration tool (alembic, ...) instead of
    DDL executed at boot."""
    with pool.connection() as conn:
        conn.execute(DDL)
