package queries_test

import (
	"context"
	"testing"

	"github.com/freakjazz/clean-api-go/application/queries"
)

func TestGetProductsPage_FirstPageHasNextCursor(t *testing.T) {
	h := queries.NewGetProductsPageQueryHandler(seedRepo())
	result, err := h.Handle(context.Background(), queries.GetProductsPageQuery{PageSize: 2})
	if err != nil {
		t.Fatalf("unexpected error: %+v", err)
	}
	if len(result.Items) != 2 {
		t.Fatalf("expected 2 items, got %d", len(result.Items))
	}
	if result.NextCursor == "" {
		t.Fatal("expected a next cursor since 5 seeded products > page size 2")
	}
}

func TestGetProductsPage_WalkAllPagesNoDuplicatesNoGaps(t *testing.T) {
	h := queries.NewGetProductsPageQueryHandler(seedRepo())

	seen := map[string]bool{}
	cursor := ""
	for i := 0; i < 10; i++ { // hard cap so a bug can't infinite-loop the test
		result, err := h.Handle(context.Background(), queries.GetProductsPageQuery{PageSize: 2, Cursor: cursor})
		if err != nil {
			t.Fatalf("unexpected error: %+v", err)
		}
		for _, p := range result.Items {
			if seen[p.ID] {
				t.Fatalf("product %s returned twice across pages — keyset pagination must never repeat a row", p.ID)
			}
			seen[p.ID] = true
		}
		if result.NextCursor == "" {
			break
		}
		cursor = result.NextCursor
	}
	if len(seen) != 5 {
		t.Fatalf("expected to see all 5 seeded products walking the cursor, got %d", len(seen))
	}
}

func TestGetProductsPage_LastPageHasNoNextCursor(t *testing.T) {
	h := queries.NewGetProductsPageQueryHandler(seedRepo())
	result, err := h.Handle(context.Background(), queries.GetProductsPageQuery{PageSize: 10})
	if err != nil {
		t.Fatalf("unexpected error: %+v", err)
	}
	if len(result.Items) != 5 {
		t.Fatalf("expected all 5 products in one page, got %d", len(result.Items))
	}
	if result.NextCursor != "" {
		t.Fatal("expected no next cursor when the page already covers every row")
	}
}

func TestGetProductsPage_InvalidCursorIsRejected(t *testing.T) {
	h := queries.NewGetProductsPageQueryHandler(seedRepo())
	_, err := h.Handle(context.Background(), queries.GetProductsPageQuery{PageSize: 2, Cursor: "not-a-valid-cursor!!!"})
	if err == nil {
		t.Fatal("expected an error for a malformed cursor")
	}
}
