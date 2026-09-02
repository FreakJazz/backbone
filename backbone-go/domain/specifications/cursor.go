// Package specifications provides Criteria pattern for flexible queries
package specifications

import (
	"encoding/base64"
	"encoding/json"
	"fmt"
)

// cursorPayload is the JSON shape encoded inside a cursor token.
type cursorPayload struct {
	V  interface{} `json:"v"`  // sort field's value on the last row of the previous page
	ID string      `json:"id"` // that row's unique id
}

// EncodeCursor returns an opaque, URL-safe token identifying a position in
// a keyset-paginated result set — the alternative to LIMIT/OFFSET that
// doesn't degrade as the offset grows: instead of "skip 50,000 rows, then
// return 20", a keyset query says "give me the 20 rows right after this
// one", which Postgres can satisfy with a direct index seek regardless of
// how deep into the result set that is.
//
// sortValue is whatever the query's sort field held on the last row of the
// page just returned (anything encoding/json can round-trip: a number,
// string, bool, or time formatted as a string). id is that row's unique
// identifier — required because the sort field alone can tie (two products
// at the same price); without a tiebreaker, a tie could make keyset
// pagination skip or repeat rows across pages.
//
// Treat the token as a black box: its shape isn't part of the contract,
// and it is not signed or encrypted — a client can decode it, so don't put
// anything in sortValue that shouldn't be visible to them (it's already
// visible in the row that produced it, so this is normally a non-issue).
func EncodeCursor(sortValue interface{}, id string) (string, error) {
	raw, err := json.Marshal(cursorPayload{V: sortValue, ID: id})
	if err != nil {
		return "", fmt.Errorf("encode cursor: %w", err)
	}
	return base64.RawURLEncoding.EncodeToString(raw), nil
}

// DecodeCursor parses a token produced by EncodeCursor. sortValue comes
// back typed the way encoding/json decodes into interface{} (float64 for
// any JSON number, otherwise string/bool/nil) — the caller, which knows
// the sort field's real column type, is responsible for converting it to
// that type before binding it as a query parameter. That mirrors how
// FilterParam values are already converted from raw query-string text to
// a concrete type (parseScalar) before reaching a Specification: type
// coercion for a dynamic field belongs to the caller who knows the schema,
// not to this generic package.
func DecodeCursor(token string) (sortValue interface{}, id string, err error) {
	raw, err := base64.RawURLEncoding.DecodeString(token)
	if err != nil {
		return nil, "", fmt.Errorf("invalid cursor: %w", err)
	}
	var payload cursorPayload
	if err := json.Unmarshal(raw, &payload); err != nil {
		return nil, "", fmt.Errorf("invalid cursor: %w", err)
	}
	if payload.ID == "" {
		return nil, "", fmt.Errorf("invalid cursor: missing id")
	}
	return payload.V, payload.ID, nil
}
