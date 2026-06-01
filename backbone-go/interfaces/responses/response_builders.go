// Package responses provides response builders for APIs
package responses

import (
	"time"

	"github.com/google/uuid"
)

// ProcessResponse represents a successful process response
type ProcessResponse struct {
	Status     string                 `json:"status"`
	StatusCode int                    `json:"status_code"`
	Message    string                 `json:"message"`
	Timestamp  string                 `json:"timestamp"`
	RequestID  string                 `json:"request_id"`
	Data       map[string]interface{} `json:"data,omitempty"`
}

// ProcessResponseBuilder builds process responses (CREATE/UPDATE/DELETE)
type processResponseBuilder struct{}

// ProcessResponseBuilder is the singleton instance
var ProcessResponseBuilder = &processResponseBuilder{}

// Success creates a successful process response
func (b *processResponseBuilder) Success(message string, data map[string]interface{}, statusCode int) ProcessResponse {
	return ProcessResponse{
		Status:     "success",
		StatusCode: statusCode,
		Message:    message,
		Timestamp:  time.Now().UTC().Format(time.RFC3339),
		RequestID:  uuid.New().String(),
		Data:       data,
	}
}

// Created creates a creation response (201)
func (b *processResponseBuilder) Created(message string, entityID string) ProcessResponse {
	return b.Success(message, map[string]interface{}{"id": entityID}, 201)
}

// Updated creates an update response (200)
func (b *processResponseBuilder) Updated(message string, data map[string]interface{}) ProcessResponse {
	return b.Success(message, data, 200)
}

// Deleted creates a deletion response (200)
func (b *processResponseBuilder) Deleted(message string, resourceID string) ProcessResponse {
	data := map[string]interface{}{}
	if resourceID != "" {
		data["resource_id"] = resourceID
	}
	return b.Success(message, data, 200)
}

// Completed creates a completion response (200)
func (b *processResponseBuilder) Completed(message string) ProcessResponse {
	return b.Success(message, nil, 200)
}

// Status creates a status response (200)
func (b *processResponseBuilder) Status(message string, data map[string]interface{}) ProcessResponse {
	return b.Success(message, data, 200)
}

// QueryResponse represents a successful query response
type QueryResponse struct {
	Status     string                   `json:"status"`
	StatusCode int                      `json:"status_code"`
	Message    string                   `json:"message"`
	Timestamp  string                   `json:"timestamp"`
	RequestID  string                   `json:"request_id"`
	Data       []map[string]interface{} `json:"data"`
	Pagination *PaginationInfo          `json:"pagination,omitempty"`
}

// PaginationInfo contains pagination metadata
type PaginationInfo struct {
	Page         int `json:"page"`
	PageSize     int `json:"page_size"`
	TotalRecords int `json:"total_records"`
	TotalPages   int `json:"total_pages"`
}

// QueryResponseBuilder builds query responses (READ/GET)
type queryResponseBuilder struct{}

// QueryResponseBuilder is the singleton instance
var QueryResponseBuilder = &queryResponseBuilder{}

// Success creates a successful query response
func (b *queryResponseBuilder) Success(message string, data []map[string]interface{}) QueryResponse {
	return QueryResponse{
		Status:     "success",
		StatusCode: 200,
		Message:    message,
		Timestamp:  time.Now().UTC().Format(time.RFC3339),
		RequestID:  uuid.New().String(),
		Data:       data,
	}
}

// SuccessWithPagination creates a paginated query response
func (b *queryResponseBuilder) SuccessWithPagination(
	message string,
	data []map[string]interface{},
	page, pageSize, totalRecords int,
) QueryResponse {
	totalPages := (totalRecords + pageSize - 1) / pageSize

	return QueryResponse{
		Status:     "success",
		StatusCode: 200,
		Message:    message,
		Timestamp:  time.Now().UTC().Format(time.RFC3339),
		RequestID:  uuid.New().String(),
		Data:       data,
		Pagination: &PaginationInfo{
			Page:         page,
			PageSize:     pageSize,
			TotalRecords: totalRecords,
			TotalPages:   totalPages,
		},
	}
}

// Single creates a response for a single resource
func (b *queryResponseBuilder) Single(message string, data map[string]interface{}) QueryResponse {
	return QueryResponse{
		Status:     "success",
		StatusCode: 200,
		Message:    message,
		Timestamp:  time.Now().UTC().Format(time.RFC3339),
		RequestID:  uuid.New().String(),
		Data:       []map[string]interface{}{data},
	}
}

// Empty creates an empty response (no results)
func (b *queryResponseBuilder) Empty(message string) QueryResponse {
	return QueryResponse{
		Status:     "success",
		StatusCode: 200,
		Message:    message,
		Timestamp:  time.Now().UTC().Format(time.RFC3339),
		RequestID:  uuid.New().String(),
		Data:       []map[string]interface{}{},
	}
}

// ErrorResponse represents an error response
type ErrorResponse struct {
	Status       string                 `json:"status"`
	StatusCode   int                    `json:"status_code"`
	Message      string                 `json:"message"`
	Timestamp    string                 `json:"timestamp"`
	RequestID    string                 `json:"request_id"`
	ErrorDetails map[string]interface{} `json:"error_details,omitempty"`
}

// ErrorResponseBuilder builds error responses
type errorResponseBuilder struct{}

// ErrorResponseBuilder is the singleton instance
var ErrorResponseBuilder = &errorResponseBuilder{}

// FromException creates an error response from an exception
func (b *errorResponseBuilder) FromException(err error) ErrorResponse {
	// Try to extract exception details if it's a BaseKernelException
	// For simplicity, we'll create a basic error response
	return ErrorResponse{
		Status:     "error",
		StatusCode: 500,
		Message:    err.Error(),
		Timestamp:  time.Now().UTC().Format(time.RFC3339),
		RequestID:  uuid.New().String(),
		ErrorDetails: map[string]interface{}{
			"error": err.Error(),
		},
	}
}

// BadRequest creates a 400 Bad Request response
func (b *errorResponseBuilder) BadRequest(message string, details map[string]interface{}) ErrorResponse {
	return ErrorResponse{
		Status:       "error",
		StatusCode:   400,
		Message:      message,
		Timestamp:    time.Now().UTC().Format(time.RFC3339),
		RequestID:    uuid.New().String(),
		ErrorDetails: details,
	}
}

// Unauthorized creates a 401 Unauthorized response
func (b *errorResponseBuilder) Unauthorized(message string) ErrorResponse {
	return ErrorResponse{
		Status:     "error",
		StatusCode: 401,
		Message:    message,
		Timestamp:  time.Now().UTC().Format(time.RFC3339),
		RequestID:  uuid.New().String(),
	}
}

// Forbidden creates a 403 Forbidden response
func (b *errorResponseBuilder) Forbidden(message string) ErrorResponse {
	return ErrorResponse{
		Status:     "error",
		StatusCode: 403,
		Message:    message,
		Timestamp:  time.Now().UTC().Format(time.RFC3339),
		RequestID:  uuid.New().String(),
	}
}

// NotFound creates a 404 Not Found response
func (b *errorResponseBuilder) NotFound(message string, resourceType, resourceID string) ErrorResponse {
	return ErrorResponse{
		Status:     "error",
		StatusCode: 404,
		Message:    message,
		Timestamp:  time.Now().UTC().Format(time.RFC3339),
		RequestID:  uuid.New().String(),
		ErrorDetails: map[string]interface{}{
			"resource_type": resourceType,
			"resource_id":   resourceID,
		},
	}
}

// InternalServerError creates a 500 Internal Server Error response
func (b *errorResponseBuilder) InternalServerError() ErrorResponse {
	return ErrorResponse{
		Status:     "error",
		StatusCode: 500,
		Message:    "Internal server error",
		Timestamp:  time.Now().UTC().Format(time.RFC3339),
		RequestID:  uuid.New().String(),
	}
}

// ServiceUnavailable creates a 503 Service Unavailable response
func (b *errorResponseBuilder) ServiceUnavailable(message string) ErrorResponse {
	return ErrorResponse{
		Status:     "error",
		StatusCode: 503,
		Message:    message,
		Timestamp:  time.Now().UTC().Format(time.RFC3339),
		RequestID:  uuid.New().String(),
	}
}
