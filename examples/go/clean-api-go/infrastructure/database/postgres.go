// Package database wires the two real backing stores this example uses:
// PostgreSQL for the Product catalog (relational, consistency-critical
// stock counter) and MongoDB for Sales/StockMovements (append-only event
// logs, schema-light by nature).
package database

import (
	"context"
	"fmt"
	"time"

	"github.com/jackc/pgx/v5/pgxpool"
)

// ConnectPostgres opens a pooled connection and verifies it with a ping.
func ConnectPostgres(ctx context.Context, dsn string) (*pgxpool.Pool, error) {
	cfg, err := pgxpool.ParseConfig(dsn)
	if err != nil {
		return nil, fmt.Errorf("parse postgres dsn: %w", err)
	}
	cfg.MaxConns = 10
	cfg.MinConns = 2 // keep a couple of connections warm so a cold pool doesn't cost a TCP+TLS handshake on the first request after idle
	cfg.MaxConnLifetime = time.Hour
	cfg.MaxConnIdleTime = 30 * time.Minute

	pool, err := pgxpool.NewWithConfig(ctx, cfg)
	if err != nil {
		return nil, fmt.Errorf("connect postgres: %w", err)
	}

	pingCtx, cancel := context.WithTimeout(ctx, 5*time.Second)
	defer cancel()
	if err := pool.Ping(pingCtx); err != nil {
		pool.Close()
		return nil, fmt.Errorf("ping postgres: %w", err)
	}
	return pool, nil
}

// MigrateProducts creates the products table if it doesn't exist yet.
//
// This inline CREATE TABLE is deliberately simple for a runnable example.
// A real service should own its schema with a versioned migration tool
// (golang-migrate, atlas, goose, ...) instead of an idempotent DDL block
// executed at boot.
func MigrateProducts(ctx context.Context, pool *pgxpool.Pool) error {
	const ddl = `
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
`
	_, err := pool.Exec(ctx, ddl)
	if err != nil {
		return fmt.Errorf("migrate products table: %w", err)
	}
	return nil
}
