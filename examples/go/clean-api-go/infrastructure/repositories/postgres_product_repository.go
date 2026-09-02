package repositories

import (
	"context"
	"errors"
	"fmt"
	"strings"
	"time"

	"github.com/FreakJazz/backbone/backbone-go/domain/specifications"
	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/pgxpool"

	"github.com/freakjazz/clean-api-go/domain/entities"
	domainrepos "github.com/freakjazz/clean-api-go/domain/repositories"
)

// cursorSortableFields lists the columns FindPageByCursor is allowed to
// order and seek by. Kept separate from specifications.ValidSortFields
// (which governs offset pagination) since every field here also needs a
// coerceCursorValue/cursorValueFor case below.
var cursorSortableFields = map[string]bool{
	"name": true, "category": true, "status": true, "price": true, "stock": true, "created_at": true,
}

const productColumns = "id, name, price, category, status, description, stock, created_at, updated_at"

// PostgresProductRepository is the production implementation of
// IProductRepository. MemoryProductRepository (same package) remains as the
// fast, dependency-free fake the unit tests under tests/application use —
// this is the real one main.go wires up.
type PostgresProductRepository struct {
	pool *pgxpool.Pool
}

var _ domainrepos.IProductRepository = (*PostgresProductRepository)(nil)

func NewPostgresProductRepository(pool *pgxpool.Pool) *PostgresProductRepository {
	return &PostgresProductRepository{pool: pool}
}

func (r *PostgresProductRepository) Save(ctx context.Context, p *entities.Product) (*entities.Product, error) {
	const q = `
INSERT INTO products (id, name, price, category, status, description, stock, created_at, updated_at)
VALUES ($1, $2, $3, $4, $5, $6, $7, $8, now())
ON CONFLICT (id) DO UPDATE SET
    name = EXCLUDED.name, price = EXCLUDED.price, category = EXCLUDED.category,
    status = EXCLUDED.status, description = EXCLUDED.description, stock = EXCLUDED.stock,
    updated_at = now()
RETURNING updated_at`
	err := r.pool.QueryRow(ctx, q, p.ID, p.Name, p.Price, p.Category, p.Status, p.Description, p.Stock, p.CreatedAt).Scan(&p.UpdatedAt)
	if err != nil {
		return nil, fmt.Errorf("save product: %w", err)
	}
	return p, nil
}

func (r *PostgresProductRepository) FindByID(ctx context.Context, id string) (*entities.Product, error) {
	row := r.pool.QueryRow(ctx, "SELECT "+productColumns+" FROM products WHERE id = $1", id)
	return scanProduct(row)
}

func (r *PostgresProductRepository) FindByName(ctx context.Context, name string) (*entities.Product, error) {
	row := r.pool.QueryRow(ctx, "SELECT "+productColumns+" FROM products WHERE lower(name) = lower($1)", name)
	p, err := scanProduct(row)
	if errors.Is(err, pgx.ErrNoRows) {
		return nil, nil
	}
	return p, err
}

// FindByCriteria translates the backbone-go Criteria (built from ?filters=
// query params) into a real parameterized SQL query — no in-memory
// filtering, no pulling the whole table to scan it row by row in Go, unlike
// MemoryProductRepository's test-only equivalent.
//
// The total match count rides along as an extra COUNT(*) OVER() column on
// the same query, computed by Postgres from the same index scan that
// produces the page. That's one round trip instead of two (SELECT + a
// separate COUNT(*) query) — with a growing table, halving the number of
// round trips per list request matters far more than any in-process
// micro-optimization.
func (r *PostgresProductRepository) FindByCriteria(ctx context.Context, criteria *specifications.Criteria) ([]*entities.Product, int, error) {
	sql, args := buildProductQuery(criteria)
	rows, err := r.pool.Query(ctx, sql, args...)
	if err != nil {
		return nil, 0, fmt.Errorf("find products by criteria: %w", err)
	}
	defer rows.Close()

	products := make([]*entities.Product, 0)
	total := 0
	for rows.Next() {
		p, rowTotal, err := scanProductRowsWithCount(rows)
		if err != nil {
			return nil, 0, err
		}
		products = append(products, p)
		total = rowTotal
	}
	if err := rows.Err(); err != nil {
		return nil, 0, err
	}

	if len(products) == 0 && criteria.Offset > 0 {
		// Page beyond the last one: COUNT(*) OVER() had nothing to ride on
		// since zero rows came back, so fall back to a plain COUNT(*) for
		// this (rare — client asked past the end) case only.
		total, err = r.countByCriteria(ctx, criteria)
		if err != nil {
			return nil, 0, err
		}
	}
	return products, total, nil
}

func (r *PostgresProductRepository) countByCriteria(ctx context.Context, criteria *specifications.Criteria) (int, error) {
	whereClause, args, _, _ := criteria.ToSQL()
	whereClause = rebindPlaceholders(whereClause)
	query := "SELECT COUNT(*) FROM products"
	if whereClause != "" {
		query += " WHERE " + whereClause
	}
	var total int
	if err := r.pool.QueryRow(ctx, query, args...).Scan(&total); err != nil {
		return 0, fmt.Errorf("count products: %w", err)
	}
	return total, nil
}

// FindPageByCursor seeks directly to the row after afterCursor via a
// (sortField, id) keyset condition instead of OFFSET — the difference that
// matters once a client pages deep into a large result set: OFFSET still
// has to scan and discard every skipped row no matter how large it gets,
// while this goes straight to the right place through the index.
//
// It fetches one row more than limit to know, for free, whether there is a
// next page — no separate COUNT or existence check needed.
func (r *PostgresProductRepository) FindPageByCursor(ctx context.Context, criteria *specifications.Criteria, sortField string, desc bool, afterCursor string, limit int) ([]*entities.Product, string, error) {
	if !cursorSortableFields[sortField] {
		sortField = "created_at"
		desc = true
	}
	if limit <= 0 || limit > specifications.MaxPageSize {
		limit = specifications.DefaultPageSize
	}

	query := "SELECT " + productColumns + " FROM products"
	args := []interface{}{}
	whereSQL := ""
	if criteria != nil && criteria.Specification != nil {
		whereSQL, args = criteria.Specification.ToSQL()
	}

	if afterCursor != "" {
		rawValue, id, err := specifications.DecodeCursor(afterCursor)
		if err != nil {
			return nil, "", err
		}
		sortValue, err := coerceCursorValue(sortField, rawValue)
		if err != nil {
			return nil, "", err
		}
		op := ">"
		if desc {
			op = "<"
		}
		keysetClause := fmt.Sprintf("(%s, id) %s (?, ?)", sortField, op)
		if whereSQL != "" {
			whereSQL = fmt.Sprintf("(%s) AND %s", whereSQL, keysetClause)
		} else {
			whereSQL = keysetClause
		}
		args = append(args, sortValue, id)
	}

	if whereSQL != "" {
		query += " WHERE " + whereSQL
	}
	direction := "ASC"
	if desc {
		direction = "DESC"
	}
	// Tie-break by id so rows with an equal sortField value (e.g. two
	// products at the same price) still get a total order — without it,
	// the keyset condition above could skip or repeat a tied row.
	query += fmt.Sprintf(" ORDER BY %s %s, id %s LIMIT %d", sortField, direction, direction, limit+1)
	query = rebindPlaceholders(query)

	rows, err := r.pool.Query(ctx, query, args...)
	if err != nil {
		return nil, "", fmt.Errorf("find products by cursor: %w", err)
	}
	defer rows.Close()

	products := make([]*entities.Product, 0, limit+1)
	for rows.Next() {
		p, err := scanProduct(rows)
		if err != nil {
			return nil, "", err
		}
		products = append(products, p)
	}
	if err := rows.Err(); err != nil {
		return nil, "", err
	}

	nextCursor := ""
	if len(products) > limit {
		products = products[:limit]
		last := products[len(products)-1]
		nextCursor, err = specifications.EncodeCursor(cursorValueFor(sortField, last), last.ID)
		if err != nil {
			return nil, "", err
		}
	}
	return products, nextCursor, nil
}

// coerceCursorValue converts a cursor's decoded JSON value (float64 for any
// number, otherwise string) into the Go type pgx needs to bind against
// sortField's real column type. This is exactly the same kind of
// caller-knows-the-schema conversion FilterParam values already go through
// (raw query-string text → int64/float64/string) before reaching a
// Specification — the generic cursor package can't know column types, so
// the repository that does is where this belongs.
func coerceCursorValue(sortField string, v interface{}) (interface{}, error) {
	switch sortField {
	case "price":
		f, ok := v.(float64)
		if !ok {
			return nil, fmt.Errorf("invalid cursor: expected a number for %q", sortField)
		}
		return f, nil
	case "stock":
		f, ok := v.(float64)
		if !ok {
			return nil, fmt.Errorf("invalid cursor: expected a number for %q", sortField)
		}
		return int(f), nil
	case "created_at":
		s, ok := v.(string)
		if !ok {
			return nil, fmt.Errorf("invalid cursor: expected a timestamp string for %q", sortField)
		}
		t, err := time.Parse(time.RFC3339Nano, s)
		if err != nil {
			return nil, fmt.Errorf("invalid cursor timestamp: %w", err)
		}
		return t, nil
	default: // name, category, status
		s, ok := v.(string)
		if !ok {
			return nil, fmt.Errorf("invalid cursor: expected a string for %q", sortField)
		}
		return s, nil
	}
}

// cursorValueFor extracts sortField's native value from p, for encoding
// the token that identifies p's position for the next page.
func cursorValueFor(sortField string, p *entities.Product) interface{} {
	switch sortField {
	case "price":
		return p.Price
	case "stock":
		return p.Stock
	case "created_at":
		return p.CreatedAt.Format(time.RFC3339Nano)
	case "category":
		return p.Category
	case "status":
		return p.Status
	default: // name
		return p.Name
	}
}

func (r *PostgresProductRepository) Delete(ctx context.Context, id string) error {
	_, err := r.pool.Exec(ctx, "DELETE FROM products WHERE id = $1", id)
	if err != nil {
		return fmt.Errorf("delete product: %w", err)
	}
	return nil
}

func (r *PostgresProductRepository) Exists(ctx context.Context, id string) bool {
	var exists bool
	_ = r.pool.QueryRow(ctx, "SELECT EXISTS(SELECT 1 FROM products WHERE id = $1)", id).Scan(&exists)
	return exists
}

// AdjustStock applies delta atomically in a single round trip: the WHERE
// guard (stock + delta >= 0) makes the check-and-update race-free without
// a transaction or SELECT ... FOR UPDATE — two concurrent sales racing for
// the last unit will see exactly one UPDATE match.
func (r *PostgresProductRepository) AdjustStock(ctx context.Context, id string, delta int) (int, error) {
	const q = `
UPDATE products SET stock = stock + $1, updated_at = now()
WHERE id = $2 AND stock + $1 >= 0
RETURNING stock`
	var newStock int
	err := r.pool.QueryRow(ctx, q, delta, id).Scan(&newStock)
	if errors.Is(err, pgx.ErrNoRows) {
		// Either the product doesn't exist, or the guard failed. Distinguish
		// them with one extra existence check so callers get an accurate error.
		if !r.Exists(ctx, id) {
			return 0, fmt.Errorf("product not found")
		}
		return 0, domainrepos.ErrInsufficientStock
	}
	if err != nil {
		return 0, fmt.Errorf("adjust stock: %w", err)
	}
	return newStock, nil
}

// ── scanning helpers ─────────────────────────────────────────────────────────

type rowScanner interface {
	Scan(dest ...interface{}) error
}

func scanProduct(row rowScanner) (*entities.Product, error) {
	var p entities.Product
	err := row.Scan(&p.ID, &p.Name, &p.Price, &p.Category, &p.Status, &p.Description, &p.Stock, &p.CreatedAt, &p.UpdatedAt)
	if errors.Is(err, pgx.ErrNoRows) {
		return nil, nil
	}
	if err != nil {
		return nil, fmt.Errorf("scan product: %w", err)
	}
	return &p, nil
}

// scanProductRowsWithCount scans a row from buildProductQuery, which appends
// a trailing COUNT(*) OVER() column to every row.
func scanProductRowsWithCount(rows pgx.Rows) (*entities.Product, int, error) {
	var p entities.Product
	var total int
	err := rows.Scan(&p.ID, &p.Name, &p.Price, &p.Category, &p.Status, &p.Description, &p.Stock, &p.CreatedAt, &p.UpdatedAt, &total)
	if err != nil {
		return nil, 0, fmt.Errorf("scan product row: %w", err)
	}
	return &p, total, nil
}

// ── Criteria → SQL ───────────────────────────────────────────────────────────

// buildProductQuery assembles the full SELECT using Criteria.GetFullSQL,
// then rebinds backbone-go's "?" placeholders to Postgres's positional
// "$1, $2, ..." syntax (backbone-go's Specification.ToSQL is driver-agnostic
// and targets the widely-used "?" convention; pgx requires "$n").
func buildProductQuery(criteria *specifications.Criteria) (string, []interface{}) {
	base := "SELECT " + productColumns + ", COUNT(*) OVER() AS full_count FROM products"
	query, args := criteria.GetFullSQL(base)
	return rebindPlaceholders(query), args
}

func rebindPlaceholders(query string) string {
	if !strings.Contains(query, "?") {
		return query
	}
	var b strings.Builder
	n := 0
	for _, r := range query {
		if r == '?' {
			n++
			fmt.Fprintf(&b, "$%d", n)
			continue
		}
		b.WriteRune(r)
	}
	return b.String()
}
