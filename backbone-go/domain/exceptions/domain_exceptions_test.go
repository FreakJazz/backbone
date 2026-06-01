package exceptions_test

import (
	"testing"

	"github.com/freakjazz/backbone-go/domain/exceptions"
	"github.com/stretchr/testify/assert"
)

func TestNewDomainException(t *testing.T) {
	tests := []struct {
		name        string
		code        int
		message     string
		details     map[string]interface{}
		shouldPanic bool
	}{
		{
			name:        "Valid domain exception",
			code:        11001001,
			message:     "Business rule violated",
			details:     map[string]interface{}{"field": "age"},
			shouldPanic: false,
		},
		{
			name:        "Code too low",
			code:        10999999,
			message:     "Invalid code",
			details:     nil,
			shouldPanic: true,
		},
		{
			name:        "Code too high",
			code:        12000000,
			message:     "Invalid code",
			details:     nil,
			shouldPanic: true,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			if tt.shouldPanic {
				assert.Panics(t, func() {
					exceptions.NewDomainException(tt.code, tt.message, tt.details)
				})
			} else {
				ex := exceptions.NewDomainException(tt.code, tt.message, tt.details)
				assert.NotNil(t, ex)
				assert.Equal(t, tt.code, ex.Code)
				assert.Equal(t, tt.message, ex.Message)
				assert.Equal(t, 400, ex.HTTPCode)
				assert.Equal(t, "domain", ex.Layer)
			}
		})
	}
}

func TestBusinessRuleViolationException(t *testing.T) {
	ex := exceptions.NewBusinessRuleViolationException(
		"User must be 18 or older",
		"ValidateUserAge",
	)

	assert.NotNil(t, ex)
	assert.Equal(t, 11001001, ex.Code)
	assert.Equal(t, "User must be 18 or older", ex.Message)
	assert.Equal(t, "ValidateUserAge", ex.RuleName)
	assert.Equal(t, "ValidateUserAge", ex.Details["rule_violated"])
}

func TestInvalidEntityStateException(t *testing.T) {
	ex := exceptions.NewInvalidEntityStateException(
		"User is inactive",
		"User",
		"user-123",
		"inactive",
		"active",
	)

	assert.NotNil(t, ex)
	assert.Equal(t, 11002001, ex.Code)
	assert.Equal(t, 412, ex.HTTPCode)
	assert.Equal(t, "User", ex.EntityType)
	assert.Equal(t, "user-123", ex.EntityID)
	assert.Equal(t, "inactive", ex.CurrentState)
	assert.Equal(t, "active", ex.RequiredState)
}

func TestInvalidValueObjectException(t *testing.T) {
	ex := exceptions.NewInvalidValueObjectException(
		"Invalid email format",
		"Email",
		"invalid-email",
	)

	assert.NotNil(t, ex)
	assert.Equal(t, 11003001, ex.Code)
	assert.Equal(t, "Email", ex.ValueObjectType)
	assert.Equal(t, "invalid-email", ex.InvalidValue)
}

func TestExceptionToDict(t *testing.T) {
	ex := exceptions.NewDomainException(
		11001001,
		"Test error",
		map[string]interface{}{"key": "value"},
	)

	dict := ex.ToDict()

	assert.NotNil(t, dict)
	assert.Equal(t, 11001001, dict["error_code"])
	assert.Equal(t, "Test error", dict["error_message"])
	assert.Equal(t, 400, dict["http_code"])
	assert.Equal(t, "domain", dict["layer"])
	assert.NotNil(t, dict["error_details"])
}

func TestExceptionError(t *testing.T) {
	ex := exceptions.NewDomainException(
		11001001,
		"Test error",
		nil,
	)

	errorStr := ex.Error()
	assert.Contains(t, errorStr, "domain")
	assert.Contains(t, errorStr, "11001001")
	assert.Contains(t, errorStr, "Test error")
}
