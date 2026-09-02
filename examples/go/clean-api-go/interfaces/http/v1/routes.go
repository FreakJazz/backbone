package v1

import (
	"net/http"
	"strings"

	"github.com/freakjazz/clean-api-go/interfaces/http/handlers"
)

func RegisterRoutes(
	mux *http.ServeMux,
	cmd *handlers.ProductCommandHandler,
	qry *handlers.ProductQueryHandler,
	sales *handlers.SaleHandler,
	movements *handlers.StockMovementHandler,
) {
	mux.HandleFunc("/api/v1/products", func(w http.ResponseWriter, r *http.Request) {
		switch r.Method {
		case http.MethodGet:
			qry.List(w, r)
		case http.MethodPost:
			cmd.Create(w, r)
		default:
			http.Error(w, "method not allowed", http.StatusMethodNotAllowed)
		}
	})

	mux.HandleFunc("/api/v1/products/", func(w http.ResponseWriter, r *http.Request) {
		path := strings.TrimPrefix(r.URL.Path, "/api/v1/products/")
		parts := strings.Split(strings.Trim(path, "/"), "/")
		productID := parts[0]

		if len(parts) == 2 && parts[1] == "status" {
			if r.Method == http.MethodPatch {
				cmd.ChangeStatus(w, r, productID)
				return
			}
			http.Error(w, "method not allowed", http.StatusMethodNotAllowed)
			return
		}

		switch r.Method {
		case http.MethodGet:
			qry.Detail(w, r, productID)
		case http.MethodPut:
			cmd.Update(w, r, productID)
		case http.MethodDelete:
			cmd.Delete(w, r, productID)
		default:
			http.Error(w, "method not allowed", http.StatusMethodNotAllowed)
		}
	})

	// ── /api/v1/sales (Mongo transaction log) ────────────────────────────────
	mux.HandleFunc("/api/v1/sales", func(w http.ResponseWriter, r *http.Request) {
		switch r.Method {
		case http.MethodGet:
			sales.List(w, r)
		case http.MethodPost:
			sales.Register(w, r)
		default:
			http.Error(w, "method not allowed", http.StatusMethodNotAllowed)
		}
	})

	// ── /api/v1/stock-movements (Mongo transaction log) ──────────────────────
	mux.HandleFunc("/api/v1/stock-movements", func(w http.ResponseWriter, r *http.Request) {
		switch r.Method {
		case http.MethodGet:
			movements.List(w, r)
		case http.MethodPost:
			movements.Register(w, r)
		default:
			http.Error(w, "method not allowed", http.StatusMethodNotAllowed)
		}
	})
}
