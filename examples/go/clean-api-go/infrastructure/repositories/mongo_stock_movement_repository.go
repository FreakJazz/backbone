package repositories

import (
	"context"
	"fmt"

	"go.mongodb.org/mongo-driver/v2/bson"
	"go.mongodb.org/mongo-driver/v2/mongo"

	"github.com/freakjazz/clean-api-go/domain/entities"
	domainrepos "github.com/freakjazz/clean-api-go/domain/repositories"
)

type MongoStockMovementRepository struct {
	col *mongo.Collection
}

var _ domainrepos.IStockMovementRepository = (*MongoStockMovementRepository)(nil)

func NewMongoStockMovementRepository(db *mongo.Database) *MongoStockMovementRepository {
	return &MongoStockMovementRepository{col: db.Collection("stock_movements")}
}

func (r *MongoStockMovementRepository) Save(ctx context.Context, m *entities.StockMovement) (*entities.StockMovement, error) {
	if _, err := r.col.InsertOne(ctx, m); err != nil {
		return nil, fmt.Errorf("insert stock movement: %w", err)
	}
	return m, nil
}

type movementFacetResult struct {
	Data       []*entities.StockMovement `bson:"data"`
	TotalCount []struct {
		Count int `bson:"count"`
	} `bson:"totalCount"`
}

// FindByProductID uses a single $facet aggregation instead of a
// CountDocuments call followed by a Find call — see MongoSaleRepository's
// equivalent method for the rationale.
func (r *MongoStockMovementRepository) FindByProductID(ctx context.Context, productID string, page, pageSize int) ([]*entities.StockMovement, int, error) {
	if page < 1 {
		page = 1
	}
	if pageSize < 1 || pageSize > 100 {
		pageSize = 10
	}

	match := bson.M{}
	if productID != "" {
		match["product_id"] = productID
	}

	pipeline := bson.A{
		bson.D{{Key: "$match", Value: match}},
		bson.D{{Key: "$sort", Value: bson.D{{Key: "created_at", Value: -1}}}},
		bson.D{{Key: "$facet", Value: bson.D{
			{Key: "data", Value: bson.A{
				bson.D{{Key: "$skip", Value: (page - 1) * pageSize}},
				bson.D{{Key: "$limit", Value: pageSize}},
			}},
			{Key: "totalCount", Value: bson.A{
				bson.D{{Key: "$count", Value: "count"}},
			}},
		}}},
	}

	cursor, err := r.col.Aggregate(ctx, pipeline)
	if err != nil {
		return nil, 0, fmt.Errorf("aggregate stock movements: %w", err)
	}
	defer cursor.Close(ctx)

	var results []movementFacetResult
	if err := cursor.All(ctx, &results); err != nil {
		return nil, 0, fmt.Errorf("decode stock movements facet: %w", err)
	}
	if len(results) == 0 {
		return []*entities.StockMovement{}, 0, nil
	}

	total := 0
	if len(results[0].TotalCount) > 0 {
		total = results[0].TotalCount[0].Count
	}
	movements := results[0].Data
	if movements == nil {
		movements = []*entities.StockMovement{}
	}
	return movements, total, nil
}
