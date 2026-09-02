package database

import (
	"context"
	"fmt"
	"time"

	"go.mongodb.org/mongo-driver/v2/bson"
	"go.mongodb.org/mongo-driver/v2/mongo"
	"go.mongodb.org/mongo-driver/v2/mongo/options"
)

// ConnectMongo opens a client and verifies it with a ping.
func ConnectMongo(ctx context.Context, uri string) (*mongo.Client, error) {
	client, err := mongo.Connect(options.Client().ApplyURI(uri))
	if err != nil {
		return nil, fmt.Errorf("connect mongo: %w", err)
	}

	pingCtx, cancel := context.WithTimeout(ctx, 5*time.Second)
	defer cancel()
	if err := client.Ping(pingCtx, nil); err != nil {
		_ = client.Disconnect(context.Background())
		return nil, fmt.Errorf("ping mongo: %w", err)
	}
	return client, nil
}

// EnsureIndexes creates the indexes both transaction collections rely on.
// Both are queried almost exclusively by product_id ordered by recency, so
// a compound index on (product_id, created_at) covers that access pattern
// without a separate sort step.
func EnsureIndexes(ctx context.Context, db *mongo.Database) error {
	compound := mongo.IndexModel{
		Keys: bson.D{{Key: "product_id", Value: 1}, {Key: "created_at", Value: -1}},
	}
	if _, err := db.Collection("sales").Indexes().CreateOne(ctx, compound); err != nil {
		return fmt.Errorf("create sales index: %w", err)
	}
	if _, err := db.Collection("stock_movements").Indexes().CreateOne(ctx, compound); err != nil {
		return fmt.Errorf("create stock_movements index: %w", err)
	}
	return nil
}
