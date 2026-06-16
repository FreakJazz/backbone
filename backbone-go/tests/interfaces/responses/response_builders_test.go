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

// Minimal calls — no opts, RID auto-generated.

func TestErrorResponseBuilder_NotFound_NoOpts(t *testing.T) {
	resp := responses.ErrorResponseBuilder.NotFound("Product not found")

	assert.Equal(t, 404, resp.StatusCode)
	assert.Equal(t, "Product not found", resp.Message)
	assert.NotEmpty(t, resp.RID, "RID must be auto-generated when not supplied")
	assert.Equal(t, 120000004, resp.ErrorCode, "default code = AppResourceNotFound")
}

func TestErrorResponseBuilder_NotFound_WithRID(t *testing.T) {
	resp := responses.ErrorResponseBuilder.NotFound("Not found",
		responses.ErrorOpts{RID: "trace-abc"})

	assert.Equal(t, "trace-abc", resp.RID)
	assert.Equal(t, 404, resp.StatusCode)
}

func TestErrorResponseBuilder_NotFound_WithCode(t *testing.T) {
	resp := responses.ErrorResponseBuilder.NotFound("Not found",
		responses.ErrorOpts{RID: "rid-1", Code: 130000003})

	assert.Equal(t, "rid-1", resp.RID)
	assert.Equal(t, 130000003, resp.ErrorCode)
}

func TestErrorResponseBuilder_ValidationError_WithRID(t *testing.T) {
	resp := responses.ErrorResponseBuilder.ValidationError("Invalid input",
		responses.ErrorOpts{RID: "rid-x"})

	assert.Equal(t, 400, resp.StatusCode)
	assert.Equal(t, "rid-x", resp.RID)
}

func TestErrorResponseBuilder_ValidationError_NoOpts(t *testing.T) {
	resp := responses.ErrorResponseBuilder.ValidationError("Bad request")
	assert.Equal(t, 400, resp.StatusCode)
	assert.NotEmpty(t, resp.RID)
}

func TestErrorResponseBuilder_Unauthorized(t *testing.T) {
	resp := responses.ErrorResponseBuilder.Unauthorized("Token expired")
	assert.Equal(t, 401, resp.StatusCode)
	assert.NotEmpty(t, resp.RID)
}

func TestErrorResponseBuilder_Forbidden(t *testing.T) {
	resp := responses.ErrorResponseBuilder.Forbidden("Access denied")
	assert.Equal(t, 403, resp.StatusCode)
}

func TestErrorResponseBuilder_Conflict(t *testing.T) {
	resp := responses.ErrorResponseBuilder.Conflict("Already exists")
	assert.Equal(t, 409, resp.StatusCode)
}

func TestErrorResponseBuilder_InternalServerError(t *testing.T) {
	resp := responses.ErrorResponseBuilder.InternalServerError("Unexpected error")
	assert.Equal(t, 500, resp.StatusCode)
}

func TestErrorResponseBuilder_InternalServerError_DefaultMessage(t *testing.T) {
	resp := responses.ErrorResponseBuilder.InternalServerError("")
	assert.Equal(t, 500, resp.StatusCode)
	assert.Equal(t, "An unexpected error occurred", resp.Message)
}

func TestErrorResponseBuilder_ServiceUnavailable(t *testing.T) {
	resp := responses.ErrorResponseBuilder.ServiceUnavailable("Down for maintenance")
	assert.Equal(t, 503, resp.StatusCode)
}

func TestErrorResponseBuilder_FromException(t *testing.T) {
	err := assert.AnError
	resp := responses.ErrorResponseBuilder.FromException(err,
		responses.ErrorOpts{RID: "rid-xyz"})

	assert.Equal(t, 500, resp.StatusCode)
	assert.Contains(t, resp.Message, err.Error())
	assert.Equal(t, "rid-xyz", resp.RID)
}

// RID is unique when auto-generated.
func TestErrorResponseBuilder_AutoRIDIsUnique(t *testing.T) {
	r1 := responses.ErrorResponseBuilder.NotFound("x")
	r2 := responses.ErrorResponseBuilder.NotFound("x")
	assert.NotEqual(t, r1.RID, r2.RID)
}

// RID is preserved when caller supplies it.
func TestErrorResponseBuilder_SuppliedRIDPreserved(t *testing.T) {
	rid := "my-trace-id"
	resp := responses.ErrorResponseBuilder.NotFound("x", responses.ErrorOpts{RID: rid})
	assert.Equal(t, rid, resp.RID)
}

// Código siempre presente — default del catálogo si no se pasa Code.
func TestErrorResponseBuilder_DefaultCodesAlwaysPresent(t *testing.T) {
	cases := []struct {
		fn       func() responses.ErrorResponse
		wantCode int
	}{
		{func() responses.ErrorResponse { return responses.ErrorResponseBuilder.ValidationError("v") }, 130000001},
		{func() responses.ErrorResponse { return responses.ErrorResponseBuilder.NotFound("n") }, 120000004},
		{func() responses.ErrorResponse { return responses.ErrorResponseBuilder.Unauthorized("u") }, 130000006},
		{func() responses.ErrorResponse { return responses.ErrorResponseBuilder.Forbidden("f") }, 130000007},
		{func() responses.ErrorResponse { return responses.ErrorResponseBuilder.Conflict("c") }, 120000006},
		{func() responses.ErrorResponse { return responses.ErrorResponseBuilder.InternalServerError("i") }, 140000001},
		{func() responses.ErrorResponse { return responses.ErrorResponseBuilder.ServiceUnavailable("s") }, 140000005},
	}
	for _, c := range cases {
		resp := c.fn()
		assert.NotZero(t, resp.ErrorCode, "error_code never be zero")
		assert.Equal(t, c.wantCode, resp.ErrorCode)
	}
}

// El caller puede sobreescribir el código por defecto con su propio código.
func TestErrorResponseBuilder_CustomCodeOverridesDefault(t *testing.T) {
	myCode := 120000042 // código propio del sistema
	resp := responses.ErrorResponseBuilder.NotFound("not found",
		responses.ErrorOpts{Code: myCode})
	assert.Equal(t, myCode, resp.ErrorCode)
}
