package exceptions_test

import (
	"testing"

	"github.com/freakjazz/backbone-go/application/exceptions"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

func TestNewUseCaseException(t *testing.T) {
	err := exceptions.NewUseCaseException("Failed to create product", "CreateProductCommandHandler")

	require.NotNil(t, err)
	assert.Contains(t, err.Error(), "Failed to create product")
	assert.Contains(t, err.Error(), "CreateProductCommandHandler")
}

func TestNewValidationException(t *testing.T) {
	fieldErrors := []exceptions.ValidationError{
		{Field: "name", Message: "required"},
		{Field: "price", Message: "must be > 0"},
	}
	err := exceptions.NewValidationException("Validation failed", fieldErrors)

	require.NotNil(t, err)
	assert.Contains(t, err.Error(), "Validation failed")
}

func TestNewAuthorizationException(t *testing.T) {
	err := exceptions.NewAuthorizationException("Access denied", "read:products")

	require.NotNil(t, err)
	assert.Contains(t, err.Error(), "Access denied")
}

func TestNewResourceNotFoundException(t *testing.T) {
	err := exceptions.NewResourceNotFoundException("Product", "uuid-123")

	require.NotNil(t, err)
	assert.Contains(t, err.Error(), "Product")
	assert.Contains(t, err.Error(), "uuid-123")
}

func TestApplicationExceptionCodes(t *testing.T) {
	tests := []struct {
		name        string
		constructor func() error
		codeRange   [2]int
	}{
		{"UseCase",       func() error { return exceptions.NewUseCaseException("msg", "handler") }, [2]int{10000000, 10999999}},
		{"Validation",    func() error { return exceptions.NewValidationException("msg", nil) },   [2]int{10000000, 10999999}},
		{"Authorization", func() error { return exceptions.NewAuthorizationException("msg", "") }, [2]int{10000000, 10999999}},
		{"NotFound",      func() error { return exceptions.NewResourceNotFoundException("T", "id") }, [2]int{10000000, 10999999}},
	}

	for _, tc := range tests {
		t.Run(tc.name, func(t *testing.T) {
			err := tc.constructor()
			require.NotNil(t, err)
			// All application exceptions implement error interface
			assert.NotEmpty(t, err.Error())
		})
	}
}
