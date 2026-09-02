package entities

import (
	"time"

	"github.com/google/uuid"
)

// MovementType describes why stock moved. It is metadata for reporting —
// the actual delta applied to Product.Stock is always an explicit signed
// int decided by the command handler, never inferred from this string.
type MovementType string

const (
	MovementIn         MovementType = "IN"        // restock / purchase from supplier
	MovementOut        MovementType = "OUT"        // manual withdrawal, damage, loss
	MovementAdjustment MovementType = "ADJUSTMENT" // inventory-count correction (delta can be +/-)
)

// StockMovement is an append-only audit record stored in MongoDB. Products
// (the mutable, consistency-critical side) live in PostgreSQL; the history of
// *why* stock changed lives here as an event log — a natural fit for a
// document store since movements are never updated, only inserted and read.
type StockMovement struct {
	ID        string       `bson:"_id" json:"id"`
	ProductID string       `bson:"product_id" json:"product_id"`
	Type      MovementType `bson:"type" json:"type"`
	Quantity  int          `bson:"quantity" json:"quantity"` // always positive; sign is implied by Type
	Delta     int          `bson:"delta" json:"delta"`       // signed change actually applied to stock
	Reason    string       `bson:"reason,omitempty" json:"reason,omitempty"`
	CreatedAt time.Time    `bson:"created_at" json:"created_at"`
}

func NewStockMovement(productID string, movType MovementType, quantity, delta int, reason string) *StockMovement {
	return &StockMovement{
		ID:        uuid.New().String(),
		ProductID: productID,
		Type:      movType,
		Quantity:  quantity,
		Delta:     delta,
		Reason:    reason,
		CreatedAt: time.Now().UTC(),
	}
}
