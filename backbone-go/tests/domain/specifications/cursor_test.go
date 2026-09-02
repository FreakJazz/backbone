package specifications_test

import (
	"testing"

	"github.com/FreakJazz/backbone/backbone-go/domain/specifications"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

func TestCursor_RoundTrip_Numeric(t *testing.T) {
	token, err := specifications.EncodeCursor(199.99, "product-42")
	require.NoError(t, err)
	assert.NotEmpty(t, token)

	value, id, err := specifications.DecodeCursor(token)
	require.NoError(t, err)
	assert.Equal(t, 199.99, value) // JSON numbers decode as float64
	assert.Equal(t, "product-42", id)
}

func TestCursor_RoundTrip_String(t *testing.T) {
	token, err := specifications.EncodeCursor("2026-01-01T00:00:00Z", "product-1")
	require.NoError(t, err)

	value, id, err := specifications.DecodeCursor(token)
	require.NoError(t, err)
	assert.Equal(t, "2026-01-01T00:00:00Z", value)
	assert.Equal(t, "product-1", id)
}

func TestCursor_IsURLSafe(t *testing.T) {
	token, err := specifications.EncodeCursor("a value with spaces & symbols/+", "id")
	require.NoError(t, err)
	for _, r := range token {
		assert.False(t, r == '/' || r == '+' || r == '=', "token must be URL-safe, got char %q in %q", r, token)
	}
}

func TestDecodeCursor_RejectsGarbage(t *testing.T) {
	_, _, err := specifications.DecodeCursor("not-a-valid-cursor!!!")
	assert.Error(t, err)
}

func TestDecodeCursor_RejectsMissingID(t *testing.T) {
	token, err := specifications.EncodeCursor("value", "")
	require.NoError(t, err)
	_, _, err = specifications.DecodeCursor(token)
	assert.Error(t, err)
}
