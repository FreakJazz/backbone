package responses_test

import (
	"testing"

	"github.com/freakjazz/backbone-go/interfaces/responses"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

// ── ProcessResponseBuilder ──────────────────────────────────────────────────

func TestProcessResponseBuilder_Created(t *testing.T) {
	resp := responses.ProcessResponseBuilder.Created("uuid-123")
	assert.Equal(t, "uuid-123", resp.ID)
}

func TestProcessResponseBuilder_Updated(t *testing.T) {
	resp := responses.ProcessResponseBuilder.Updated("uuid-456")
	assert.Equal(t, "uuid-456", resp.ID)
}

func TestProcessResponseBuilder_Deleted(t *testing.T) {
	resp := responses.ProcessResponseBuilder.Deleted("uuid-789")
	assert.Equal(t, "uuid-789", resp.ID)
}

// ── SimpleObjectResponseBuilder ─────────────────────────────────────────────

func TestSimpleObjectResponseBuilder_Found(t *testing.T) {
	data := map[string]interface{}{"id": "1", "name": "Laptop"}
	result := responses.SimpleObjectResponseBuilder.Found(data)
	assert.Equal(t, "1", result["id"])
	assert.Equal(t, "Laptop", result["name"])
}

// ── PaginatedResponseBuilder ─────────────────────────────────────────────────

func TestPaginatedResponseBuilder_Success(t *testing.T) {
	items := []map[string]interface{}{{"id": "1"}, {"id": "2"}}
	resp := responses.PaginatedResponseBuilder.Success(items, 50, 1, 10, "Products retrieved")

	assert.Equal(t, "success", resp.Meta.Status)
	assert.Equal(t, 200, resp.Meta.StatusCode)
	assert.Equal(t, "Products retrieved", resp.Meta.Message)
	assert.Len(t, resp.Items, 2)
	assert.Equal(t, 50, resp.Pagination.TotalCount)
	assert.Equal(t, 1, resp.Pagination.Page)
	assert.Equal(t, 10, resp.Pagination.PageSize)
}

func TestPaginatedResponseBuilder_Empty(t *testing.T) {
	resp := responses.PaginatedResponseBuilder.Empty("No results")

	assert.Equal(t, "success", resp.Meta.Status)
	assert.Empty(t, resp.Items)
	assert.Equal(t, 0, resp.Pagination.TotalCount)
}

func TestPaginatedResponseBuilder_NilItemsBecomesEmpty(t *testing.T) {
	resp := responses.PaginatedResponseBuilder.Success(nil, 0, 1, 10, "Empty")
	require.NotNil(t, resp.Items)
	assert.Empty(t, resp.Items)
}

// ── ErrorResponseBuilder ──────────────────────────────────────────────────────

func TestErrorResponseBuilder_NotFound(t *testing.T) {
	resp := responses.ErrorResponseBuilder.NotFound("Product not found")

	assert.Equal(t, 404, resp.StatusCode)
	assert.Equal(t, "Product not found", resp.Message)
	assert.Equal(t, "NOT_FOUND", resp.CodeError)
	assert.NotEmpty(t, resp.RequestID)
}

func TestErrorResponseBuilder_ValidationError(t *testing.T) {
	fieldErrors := map[string]string{"name": "required", "price": "must be > 0"}
	resp := responses.ErrorResponseBuilder.ValidationError("Invalid input", fieldErrors)

	assert.Equal(t, 400, resp.StatusCode)
	assert.Equal(t, "VALIDATION_ERROR", resp.CodeError)
	assert.Equal(t, fieldErrors, resp.FieldErrors)
}

func TestErrorResponseBuilder_ValidationError_NoFields(t *testing.T) {
	resp := responses.ErrorResponseBuilder.ValidationError("Bad request", nil)
	assert.Equal(t, 400, resp.StatusCode)
	assert.Nil(t, resp.FieldErrors)
}

func TestErrorResponseBuilder_Unauthorized(t *testing.T) {
	resp := responses.ErrorResponseBuilder.Unauthorized("Token expired")
	assert.Equal(t, 401, resp.StatusCode)
	assert.Equal(t, "AUTHENTICATION_ERROR", resp.CodeError)
}

func TestErrorResponseBuilder_Forbidden(t *testing.T) {
	resp := responses.ErrorResponseBuilder.Forbidden("Access denied")
	assert.Equal(t, 403, resp.StatusCode)
	assert.Equal(t, "AUTHORIZATION_ERROR", resp.CodeError)
}

func TestErrorResponseBuilder_Conflict(t *testing.T) {
	resp := responses.ErrorResponseBuilder.Conflict("Already exists")
	assert.Equal(t, 409, resp.StatusCode)
	assert.Equal(t, "CONFLICT", resp.CodeError)
}

func TestErrorResponseBuilder_InternalServerError(t *testing.T) {
	resp := responses.ErrorResponseBuilder.InternalServerError("Unexpected error")
	assert.Equal(t, 500, resp.StatusCode)
	assert.Equal(t, "INTERNAL_SERVER_ERROR", resp.CodeError)
}

func TestErrorResponseBuilder_InternalServerError_DefaultMessage(t *testing.T) {
	resp := responses.ErrorResponseBuilder.InternalServerError("")
	assert.Equal(t, 500, resp.StatusCode)
	assert.Equal(t, "An unexpected error occurred", resp.Message)
}

func TestErrorResponseBuilder_ServiceUnavailable(t *testing.T) {
	resp := responses.ErrorResponseBuilder.ServiceUnavailable("Down for maintenance")
	assert.Equal(t, 503, resp.StatusCode)
	assert.Equal(t, "SERVICE_UNAVAILABLE", resp.CodeError)
}

func TestErrorResponseBuilder_FromException(t *testing.T) {
	err := assert.AnError
	resp := responses.ErrorResponseBuilder.FromException(err)
	assert.Equal(t, 500, resp.StatusCode)
	assert.Equal(t, "INTERNAL_SERVER_ERROR", resp.CodeError)
	assert.Contains(t, resp.Message, err.Error())
}

func TestErrorResponseBuilder_RequestIDIsUnique(t *testing.T) {
	r1 := responses.ErrorResponseBuilder.NotFound("x")
	r2 := responses.ErrorResponseBuilder.NotFound("x")
	assert.NotEqual(t, r1.RequestID, r2.RequestID)
}
