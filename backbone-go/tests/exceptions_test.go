// Tests for domain and application exceptions.
package backbone_test

import (
	"testing"

	appEx "github.com/freakjazz/backbone-go/application/exceptions"
	domEx "github.com/freakjazz/backbone-go/domain/exceptions"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

// ── Domain exceptions ─────────────────────────────────────────────────────────

func TestNewDomainException(t *testing.T) {
	tests := []struct {
		name        string
		code        int
		shouldPanic bool
	}{
		{"valid code", 11001001, false},
		{"code too low", 10999999, true},
		{"code too high", 12000000, true},
	}
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			if tt.shouldPanic {
				assert.Panics(t, func() { domEx.NewDomainException(tt.code, "msg", nil) })
			} else {
				ex := domEx.NewDomainException(tt.code, "Business rule violated", map[string]interface{}{"field": "age"})
				require.NotNil(t, ex)
				assert.Equal(t, tt.code, ex.Code)
				assert.Equal(t, 400, ex.HTTPCode)
				assert.Equal(t, "domain", ex.Layer)
			}
		})
	}
}

func TestBusinessRuleViolationException(t *testing.T) {
	ex := domEx.NewBusinessRuleViolationException("User must be 18 or older", "ValidateUserAge")
	require.NotNil(t, ex)
	assert.Equal(t, 11001001, ex.Code)
	assert.Equal(t, "ValidateUserAge", ex.RuleName)
	assert.Equal(t, "ValidateUserAge", ex.Details["rule_violated"])
}

func TestInvalidEntityStateException(t *testing.T) {
	ex := domEx.NewInvalidEntityStateException("User is inactive", "User", "user-123", "inactive", "active")
	require.NotNil(t, ex)
	assert.Equal(t, 11002001, ex.Code)
	assert.Equal(t, 412, ex.HTTPCode)
	assert.Equal(t, "inactive", ex.CurrentState)
	assert.Equal(t, "active", ex.RequiredState)
}

func TestInvalidValueObjectException(t *testing.T) {
	ex := domEx.NewInvalidValueObjectException("Invalid email", "Email", "bad-email")
	require.NotNil(t, ex)
	assert.Equal(t, 11003001, ex.Code)
	assert.Equal(t, "Email", ex.ValueObjectType)
}

func TestDomainExceptionToDict(t *testing.T) {
	ex := domEx.NewDomainException(11001001, "Test error", map[string]interface{}{"key": "val"})
	d := ex.ToDict()
	assert.Equal(t, 11001001, d["error_code"])
	assert.Equal(t, "Test error", d["error_message"])
	assert.Equal(t, "domain", d["layer"])
}

func TestDomainExceptionError(t *testing.T) {
	ex := domEx.NewDomainException(11001001, "Test error", nil)
	s := ex.Error()
	assert.Contains(t, s, "domain")
	assert.Contains(t, s, "11001001")
	assert.Contains(t, s, "Test error")
}

// ── Application exceptions ────────────────────────────────────────────────────

func TestNewUseCaseException(t *testing.T) {
	err := appEx.NewUseCaseException("Failed to create product", "CreateProductCommandHandler")
	require.NotNil(t, err)
	assert.Contains(t, err.Error(), "Failed to create product")
	assert.Equal(t, "CreateProductCommandHandler", err.Details["use_case"])
}

func TestNewValidationException(t *testing.T) {
	err := appEx.NewValidationException("Validation failed", []appEx.ValidationError{
		{Field: "email", Message: "Invalid format", Code: "INVALID_FORMAT"},
	})
	require.NotNil(t, err)
	assert.Contains(t, err.Error(), "Validation failed")
}

func TestNewAuthorizationException(t *testing.T) {
	err := appEx.NewAuthorizationException("Access denied", "read:products", "user-1")
	require.NotNil(t, err)
	assert.Contains(t, err.Error(), "Access denied")
}

func TestNewResourceNotFoundException(t *testing.T) {
	err := appEx.NewResourceNotFoundException("Product not found", "Product", "uuid-123")
	require.NotNil(t, err)
	assert.Contains(t, err.Error(), "Product not found")
	assert.Equal(t, "Product", err.Details["resource_type"])
	assert.Equal(t, "uuid-123", err.Details["resource_id"])
}
