// Package responses provides response builders for APIs.
// Contracts match backbone Python exactly.
package responses

import (
	"github.com/google/uuid"
)

// ---------------------------------------------------------------------------
// ProcessResponseBuilder  — CREATE / UPDATE / DELETE
// Returns: {"id": "uuid"}
// ---------------------------------------------------------------------------

// IDResponse is the body returned by write operations (create, update, delete).
type IDResponse struct {
	ID string `json:"id"`
}

type processResponseBuilder struct{}

// ProcessResponseBuilder is the singleton instance.
var ProcessResponseBuilder = &processResponseBuilder{}

// Created returns {"id": entityID} — use HTTP 201.
func (b *processResponseBuilder) Created(entityID string) IDResponse {
	return IDResponse{ID: entityID}
}

// Updated returns {"id": entityID} — use HTTP 200.
func (b *processResponseBuilder) Updated(entityID string) IDResponse {
	return IDResponse{ID: entityID}
}

// Deleted returns {"id": entityID} — use HTTP 200.
func (b *processResponseBuilder) Deleted(entityID string) IDResponse {
	return IDResponse{ID: entityID}
}

// ---------------------------------------------------------------------------
// SimpleObjectResponseBuilder  — GET single resource
// Returns the object directly, no wrapper.
// ---------------------------------------------------------------------------

type simpleObjectResponseBuilder struct{}

// SimpleObjectResponseBuilder is the singleton instance.
var SimpleObjectResponseBuilder = &simpleObjectResponseBuilder{}

// Found returns the data map as-is.
func (b *simpleObjectResponseBuilder) Found(data map[string]interface{}) map[string]interface{} {
	return data
}

// ---------------------------------------------------------------------------
// PaginatedResponseBuilder  — GET list
// Returns:
//
//	{
//	  "meta":       {"status": "success", "status_code": 200, "message": "..."},
//	  "items":      [{}, ...],
//	  "pagination": {"total_count": N, "page": P, "page_size": S, "total_pages": T}
//	}
// ---------------------------------------------------------------------------

// PaginatedMeta is the meta section of a paginated response.
type PaginatedMeta struct {
	Status     string `json:"status"`
	StatusCode int    `json:"status_code"`
	Message    string `json:"message"`
}

// PaginationInfo is the pagination section of a paginated response.
type PaginationInfo struct {
	TotalCount int `json:"total_count"`
	Page       int `json:"page"`
	PageSize   int `json:"page_size"`
	TotalPages int `json:"total_pages"`
}

// PaginatedResponse is the full paginated response body.
type PaginatedResponse struct {
	Meta       PaginatedMeta            `json:"meta"`
	Items      []map[string]interface{} `json:"items"`
	Pagination PaginationInfo           `json:"pagination"`
}

type paginatedResponseBuilder struct{}

// PaginatedResponseBuilder is the singleton instance.
var PaginatedResponseBuilder = &paginatedResponseBuilder{}

// Success builds a paginated response.
func (b *paginatedResponseBuilder) Success(
	items []map[string]interface{},
	totalCount, page, pageSize int,
	message string,
) PaginatedResponse {
	if items == nil {
		items = []map[string]interface{}{}
	}
	totalPages := 0
	if pageSize > 0 {
		totalPages = (totalCount + pageSize - 1) / pageSize
	}
	return PaginatedResponse{
		Meta: PaginatedMeta{
			Status:     "success",
			StatusCode: 200,
			Message:    message,
		},
		Items: items,
		Pagination: PaginationInfo{
			TotalCount: totalCount,
			Page:       page,
			PageSize:   pageSize,
			TotalPages: totalPages,
		},
	}
}

// Empty builds an empty paginated response.
func (b *paginatedResponseBuilder) Empty(message string) PaginatedResponse {
	return b.Success(nil, 0, 0, 0, message)
}

// ---------------------------------------------------------------------------
// ErrorResponseBuilder  — errors
// Returns:
//
//	{
//	  "request_id":   "uuid",
//	  "status_code":  400,
//	  "message":      "...",
//	  "code_error":   "VALIDATION_ERROR",
//	  "field_errors": {...}  // optional, validation only
//	}
// ---------------------------------------------------------------------------

// ErrorResponse is the standard error body.
type ErrorResponse struct {
	RequestID   string            `json:"request_id"`
	StatusCode  int               `json:"status_code"`
	Message     string            `json:"message"`
	CodeError   string            `json:"code_error"`
	FieldErrors map[string]string `json:"field_errors,omitempty"`
}

type errorResponseBuilder struct{}

// ErrorResponseBuilder is the singleton instance.
var ErrorResponseBuilder = &errorResponseBuilder{}

func (b *errorResponseBuilder) build(statusCode int, message, codeError string) ErrorResponse {
	return ErrorResponse{
		RequestID:  uuid.New().String(),
		StatusCode: statusCode,
		Message:    message,
		CodeError:  codeError,
	}
}

// FromException creates an error response from any error value.
func (b *errorResponseBuilder) FromException(err error) ErrorResponse {
	return b.build(500, err.Error(), "INTERNAL_SERVER_ERROR")
}

// ValidationError creates a 400 validation error, optionally with field errors.
func (b *errorResponseBuilder) ValidationError(message string, fieldErrors map[string]string) ErrorResponse {
	r := b.build(400, message, "VALIDATION_ERROR")
	r.FieldErrors = fieldErrors
	return r
}

// NotFound creates a 404 error.
func (b *errorResponseBuilder) NotFound(message string) ErrorResponse {
	return b.build(404, message, "NOT_FOUND")
}

// Unauthorized creates a 401 error.
func (b *errorResponseBuilder) Unauthorized(message string) ErrorResponse {
	return b.build(401, message, "AUTHENTICATION_ERROR")
}

// Forbidden creates a 403 error.
func (b *errorResponseBuilder) Forbidden(message string) ErrorResponse {
	return b.build(403, message, "AUTHORIZATION_ERROR")
}

// Conflict creates a 409 error.
func (b *errorResponseBuilder) Conflict(message string) ErrorResponse {
	return b.build(409, message, "CONFLICT")
}

// InternalServerError creates a 500 error.
func (b *errorResponseBuilder) InternalServerError(message string) ErrorResponse {
	if message == "" {
		message = "An unexpected error occurred"
	}
	return b.build(500, message, "INTERNAL_SERVER_ERROR")
}

// ServiceUnavailable creates a 503 error.
func (b *errorResponseBuilder) ServiceUnavailable(message string) ErrorResponse {
	return b.build(503, message, "SERVICE_UNAVAILABLE")
}
