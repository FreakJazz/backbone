package entities

import (
	"time"

	"github.com/google/uuid"
)

// Sale is an append-only record stored in MongoDB, one per completed sale.
// UnitPrice is a snapshot taken at sale time — it must never be recomputed
// from the current Product.Price, since that would silently rewrite history
// whenever the catalog price changes later.
type Sale struct {
	ID          string    `bson:"_id" json:"id"`
	ProductID   string    `bson:"product_id" json:"product_id"`
	Quantity    int       `bson:"quantity" json:"quantity"`
	UnitPrice   float64   `bson:"unit_price" json:"unit_price"`
	TotalAmount float64   `bson:"total_amount" json:"total_amount"`
	CreatedAt   time.Time `bson:"created_at" json:"created_at"`
}

func NewSale(productID string, quantity int, unitPrice float64) *Sale {
	return &Sale{
		ID:          uuid.New().String(),
		ProductID:   productID,
		Quantity:    quantity,
		UnitPrice:   unitPrice,
		TotalAmount: unitPrice * float64(quantity),
		CreatedAt:   time.Now().UTC(),
	}
}
