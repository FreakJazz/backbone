// Package v1 registers all /api/v1 routes on a ServeMux.
// Single responsibility: URL wiring. No business logic.
package v1

import (
	"net/http"
	"strings"

	"github.com/freakjazz/backbone-go/examples/clean-api-go/interfaces/http/handlers"
)

// RegisterRoutes attaches all v1 product routes to mux.
//
//	POST   /api/v1/products              → cmd.CreateProduct
//	GET    /api/v1/products              → qry.GetProducts
//	GET    /api/v1/products/{id}         → qry.GetProductByID
//	PUT    /api/v1/products/{id}         → cmd.UpdateProduct
//	DELETE /api/v1/products/{id}         → cmd.DeleteProduct
//	PATCH  /api/v1/products/{id}/status  → cmd.ChangeProductStatus
func RegisterRoutes(
	mux *http.ServeMux,
	cmd *handlers.ProductCommandHandler,
	qry *handlers.ProductQueryHandler,
) {
	// Collection
	mux.HandleFunc("/api/v1/products", func(w http.ResponseWriter, r *http.Request) {
		switch r.Method {
		case http.MethodPost:
			cmd.CreateProduct(w, r)
		case http.MethodGet:
			qry.GetProducts(w, r)
		default:
			http.Error(w, `{"error":"method not allowed"}`, http.StatusMethodNotAllowed)
		}
	})

	// Item  /api/v1/products/{id}  and  /api/v1/products/{id}/status
	mux.HandleFunc("/api/v1/products/", func(w http.ResponseWriter, r *http.Request) {
		tail := strings.TrimPrefix(r.URL.Path, "/api/v1/products/")
		parts := strings.SplitN(tail, "/", 2)
		id := parts[0]

		if id == "" {
			http.Error(w, `{"error":"product ID required"}`, http.StatusBadRequest)
			return
		}

		// /api/v1/products/{id}/status
		if len(parts) == 2 && parts[1] == "status" {
			if r.Method != http.MethodPatch {
				http.Error(w, `{"error":"method not allowed"}`, http.StatusMethodNotAllowed)
				return
			}
			cmd.ChangeProductStatus(w, r, id)
			return
		}

		// /api/v1/products/{id}
		switch r.Method {
		case http.MethodGet:
			qry.GetProductByID(w, r, id)
		case http.MethodPut:
			cmd.UpdateProduct(w, r, id)
		case http.MethodDelete:
			cmd.DeleteProduct(w, r, id)
		default:
			http.Error(w, `{"error":"method not allowed"}`, http.StatusMethodNotAllowed)
		}
	})
}
