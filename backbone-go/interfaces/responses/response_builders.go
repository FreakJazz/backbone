// Package responses provides response builders for APIs.
// Contracts match backbone Python exactly.
package responses

import (
	"strings"

	bberrors "github.com/freakjazz/backbone-go/errors"
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
		},
	}
}

// Empty builds an empty paginated response.
func (b *paginatedResponseBuilder) Empty(message string) PaginatedResponse {
	return b.Success(nil, 0, 0, 0, message)
}

// ---------------------------------------------------------------------------
// ErrorResponseBuilder  — errors
//
// error_code es SIEMPRE obligatorio en la respuesta.
// Cada método tiene un código por defecto del catálogo backbone (errors/codes.go).
// El caller puede sobreescribirlo pasando ErrorOpts{Code: miCodigo}.
//
// Catálogo de capas:
//
//	11 = Domain        → 110000001, 110000002, ...
//	12 = Application   → 120000001, 120000002, ...
//	13 = Interface     → 130000001, 130000002, ...
//	14 = Infrastructure→ 140000001, 140000002, ...
//
// Uso:
//
//	// Mínimo — código por defecto del catálogo, RID auto-generado
//	ErrorResponseBuilder.NotFound("not found")
//
//	// Con RID del contexto HTTP
//	ErrorResponseBuilder.NotFound("not found", ErrorOpts{RID: rid})
//
//	// Con código propio del sistema (sobreescribe el default)
//	ErrorResponseBuilder.ValidationError("name is required", ErrorOpts{
//	    RID:  rid,
//	    Code: 130000004, // catálogo propio de la API
//	})
//
// Respuesta:
//
//	{
//	  "rid":         "uuid",
//	  "status_code": 400,
//	  "message":     "...",
//	  "error_code":  130000001,    ← siempre presente
//	}
// ---------------------------------------------------------------------------

// ErrorOpts permite sobreescribir los valores por defecto de una respuesta de error.
type ErrorOpts struct {
	// RID es el identificador de traza HTTP (del middleware).
	// Si está vacío se genera un UUID automáticamente.
	RID string

	// Code sobreescribe el código de error por defecto del método.
	// 0 = usar el default del catálogo backbone.
	Code int
}

// ErrorResponse es el cuerpo estándar de error.
type ErrorResponse struct {
	RID        string `json:"rid"`
	StatusCode int    `json:"status_code"`
	Message    string `json:"message"`
	ErrorCode  int    `json:"error_code"`
}

type errorResponseBuilder struct{}

// ErrorResponseBuilder es la instancia singleton.
var ErrorResponseBuilder = &errorResponseBuilder{}

// build construye la respuesta. defaultCode se usa si opts no trae un código propio.
func (b *errorResponseBuilder) build(statusCode int, message string, defaultCode int, opts []ErrorOpts) ErrorResponse {
	var o ErrorOpts
	if len(opts) > 0 {
		o = opts[0]
	}
	rid := o.RID
	if rid == "" {
		rid = strings.ReplaceAll(uuid.New().String(), "-", "")
	}
	code := o.Code
	if code == 0 {
		code = defaultCode
	}
	return ErrorResponse{
		RID:        rid,
		StatusCode: statusCode,
		Message:    message,
		ErrorCode:  code,
	}
}

// FromException construye un error 500 a partir de cualquier error.
// En producción pasa un mensaje genérico para no exponer detalles internos.
func (b *errorResponseBuilder) FromException(err error, opts ...ErrorOpts) ErrorResponse {
	return b.build(500, err.Error(), bberrors.InfraDBFailure.Int(), opts)
}

// ValidationError crea un error 400.
// Default: 130000001 (Interface — invalid request body).
func (b *errorResponseBuilder) ValidationError(message string, opts ...ErrorOpts) ErrorResponse {
	return b.build(400, message, bberrors.IfcInvalidRequestBody.Int(), opts)
}

// NotFound crea un error 404.
// Default: 120000004 (Application — resource not found).
func (b *errorResponseBuilder) NotFound(message string, opts ...ErrorOpts) ErrorResponse {
	return b.build(404, message, bberrors.AppResourceNotFound.Int(), opts)
}

// Unauthorized crea un error 401.
// Default: 130000006 (Interface — unauthorized).
func (b *errorResponseBuilder) Unauthorized(message string, opts ...ErrorOpts) ErrorResponse {
	return b.build(401, message, bberrors.IfcUnauthorized.Int(), opts)
}

// Forbidden crea un error 403.
// Default: 130000007 (Interface — forbidden).
func (b *errorResponseBuilder) Forbidden(message string, opts ...ErrorOpts) ErrorResponse {
	return b.build(403, message, bberrors.IfcForbidden.Int(), opts)
}

// Conflict crea un error 409.
// Default: 120000006 (Application — conflict).
func (b *errorResponseBuilder) Conflict(message string, opts ...ErrorOpts) ErrorResponse {
	return b.build(409, message, bberrors.AppConflict.Int(), opts)
}

// InternalServerError crea un error 500.
// En sistemas bancarios usa siempre el mensaje genérico para no exponer internos.
// Default: 140000001 (Infrastructure — DB failure).
func (b *errorResponseBuilder) InternalServerError(message string, opts ...ErrorOpts) ErrorResponse {
	if message == "" {
		message = "An unexpected error occurred"
	}
	return b.build(500, message, bberrors.InfraDBFailure.Int(), opts)
}

// ServiceUnavailable crea un error 503.
// Default: 140000005 (Infrastructure — service unavailable).
func (b *errorResponseBuilder) ServiceUnavailable(message string, opts ...ErrorOpts) ErrorResponse {
	return b.build(503, message, bberrors.InfraServiceUnavailable.Int(), opts)
}
