package repositories

import (
	"context"
	"fmt"

	"go.mongodb.org/mongo-driver/v2/bson"
	"go.mongodb.org/mongo-driver/v2/mongo"

	"github.com/freakjazz/clean-api-go/domain/entities"
	domainrepos "github.com/freakjazz/clean-api-go/domain/repositories"
)

type MongoSaleRepository struct {
	col *mongo.Collection
}

var _ domainrepos.ISaleRepository = (*MongoSaleRepository)(nil)

func NewMongoSaleRepository(db *mongo.Database) *MongoSaleRepository {
	return &MongoSaleRepository{col: db.Collection("sales")}
}

func (r *MongoSaleRepository) Save(ctx context.Context, s *entities.Sale) (*entities.Sale, error) {
	if _, err := r.col.InsertOne(ctx, s); err != nil {
		return nil, fmt.Errorf("insert sale: %w", err)
	}
	return s, nil
}

// facetResult mirrors the shape of a $facet aggregation output: one branch
// holding the page of documents, one holding a single-element count.
type saleFacetResult struct {
	Data       []*entities.Sale `bson:"data"`
	TotalCount []struct {
		Count int `bson:"count"`
	} `bson:"totalCount"`
}

// FindByProductID uses a single $facet aggregation instead of a
// CountDocuments call followed by a Find call: both branches run against
// the same $match stage in one round trip to Mongo, which is what actually
// matters for latency as the collection grows — an append-only log is
// exactly the kind of collection that keeps growing indefinitely.
func (r *MongoSaleRepository) FindByProductID(ctx context.Context, productID string, page, pageSize int) ([]*entities.Sale, int, error) {
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
		return nil, 0, fmt.Errorf("aggregate sales: %w", err)
	}
	defer cursor.Close(ctx)

	var results []saleFacetResult
	if err := cursor.All(ctx, &results); err != nil {
		return nil, 0, fmt.Errorf("decode sales facet: %w", err)
	}
	if len(results) == 0 {
		return []*entities.Sale{}, 0, nil
	}

	total := 0
	if len(results[0].TotalCount) > 0 {
		total = results[0].TotalCount[0].Count
	}
	sales := results[0].Data
	if sales == nil {
		sales = []*entities.Sale{}
	}
	return sales, total, nil
}
