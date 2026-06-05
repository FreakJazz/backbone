// Package exceptions provides application layer exceptions with 8-digit error codes (10xxxxxx)
package exceptions

import (
	"fmt"
	"time"

	domainExceptions "github.com/freakjazz/backbone-go/domain/exceptions"
)

// ApplicationException represents application layer exceptions (10xxxxxx)
type ApplicationException struct {
	*domainExceptions.BaseKernelException
}

// NewApplicationException creates a new application exception
func NewApplicationException(code int, message string, details map[string]interface{}) *ApplicationException {
	if code < 10000000 || code > 10999999 {
		panic(fmt.Sprintf("Application exception code must be in range 10000000-10999999, got: %d", code))
	}

	return &ApplicationException{
		BaseKernelException: &domainExceptions.BaseKernelException{
			Code:        code,
			Message:     message,
			HTTPCode:    500,
			Details:     details,
			Layer:       "application",
			Severity:    domainExceptions.SeverityMedium,
			Timestamp:   time.Now().UTC(),
			Recoverable: true,
			Context:     make(map[string]interface{}),
		},
	}
}

// UseCaseException for use case failures
type UseCaseException struct {
	*ApplicationException
	UseCaseName string
}

// NewUseCaseException creates a use case exception
func NewUseCaseException(message, useCaseName string) *UseCaseException {
	details := map[string]interface{}{
		"use_case": useCaseName,
	}

	exception := NewApplicationException(10001001, message, details)

	return &UseCaseException{
		ApplicationException: exception,
		UseCaseName:          useCaseName,
	}
}

// ValidationError represents a single validation error
type ValidationError struct {
	Field   string `json:"field"`
	Message string `json:"message"`
	Code    string `json:"code,omitempty"`
}

// ValidationException for validation errors
type ValidationException struct {
	*ApplicationException
	ValidationErrors []ValidationError
}

// NewValidationException creates a validation exception
func NewValidationException(message string, errors []ValidationError) *ValidationException {
	details := map[string]interface{}{
		"validation_errors": errors,
	}

	exception := NewApplicationException(10002001, message, details)
	exception.HTTPCode = 400

	return &ValidationException{
		ApplicationException: exception,
		ValidationErrors:     errors,
	}
}

// AuthorizationException for authorization failures
type AuthorizationException struct {
	*ApplicationException
	RequiredPermission string
	UserID             string
}

// NewAuthorizationException creates an authorization exception
func NewAuthorizationException(message, requiredPermission, userID string) *AuthorizationException {
	details := map[string]interface{}{
		"required_permission": requiredPermission,
		"user_id":             userID,
	}

	exception := NewApplicationException(10003001, message, details)
	exception.HTTPCode = 403

	return &AuthorizationException{
		ApplicationException: exception,
		RequiredPermission:   requiredPermission,
		UserID:               userID,
	}
}

// ResourceNotFoundException for resource not found errors
type ResourceNotFoundException struct {
	*ApplicationException
	ResourceType string
	ResourceID   string
}

// NewResourceNotFoundException creates a resource not found exception
func NewResourceNotFoundException(message, resourceType, resourceID string) *ResourceNotFoundException {
	details := map[string]interface{}{
		"resource_type": resourceType,
		"resource_id":   resourceID,
	}

	exception := NewApplicationException(10004001, message, details)
	exception.HTTPCode = 404

	return &ResourceNotFoundException{
		ApplicationException: exception,
		ResourceType:         resourceType,
		ResourceID:           resourceID,
	}
}

// ExternalServiceException for external service failures
type ExternalServiceException struct {
	*ApplicationException
	ServiceName string
	Operation   string
}

// NewExternalServiceException creates an external service exception
func NewExternalServiceException(message, serviceName, operation string) *ExternalServiceException {
	details := map[string]interface{}{
		"service":   serviceName,
		"operation": operation,
	}

	exception := NewApplicationException(10005001, message, details)
	exception.HTTPCode = 502

	return &ExternalServiceException{
		ApplicationException: exception,
		ServiceName:          serviceName,
		Operation:            operation,
	}
}

// Application Error Codes
const (
	// Use Case Errors (10001XXX)
	UseCaseError = 10001001

	// Validation Errors (10002XXX)
	ValidationErrorCode  = 10002001
	RequiredFieldMissing = 10002002
	InvalidFieldFormat   = 10002003
	FieldOutOfRange      = 10002004

	// Authorization Errors (10003XXX)
	AuthorizationError      = 10003001
	InsufficientPermissions = 10003002
	RoleNotAuthorized       = 10003003

	// Resource Errors (10004XXX)
	ResourceNotFound = 10004001
	UserNotFound     = 10004002
	EntityNotFound   = 10004003

	// External Service Errors (10005XXX)
	ExternalServiceError     = 10005001
	PaymentGatewayError      = 10005002
	NotificationServiceError = 10005003
	GeocodingServiceError    = 10005004
)
