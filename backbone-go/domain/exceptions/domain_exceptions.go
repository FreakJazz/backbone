// Package exceptions provides domain layer exceptions with 8-digit error codes (11xxxxxx)
package exceptions

import (
	"encoding/json"
	"fmt"
	"time"
)

// ErrorSeverity represents the severity level of an error
type ErrorSeverity string

const (
	SeverityCritical ErrorSeverity = "critical"
	SeverityHigh     ErrorSeverity = "high"
	SeverityMedium   ErrorSeverity = "medium"
	SeverityLow      ErrorSeverity = "low"
)

// BaseKernelException is the base exception for all framework exceptions
type BaseKernelException struct {
	Code        int                    `json:"code"`
	Message     string                 `json:"message"`
	HTTPCode    int                    `json:"http_code"`
	Details     map[string]interface{} `json:"details,omitempty"`
	Layer       string                 `json:"layer"`
	Severity    ErrorSeverity          `json:"severity"`
	Timestamp   time.Time              `json:"timestamp"`
	Recoverable bool                   `json:"recoverable"`
	RetryAfter  *int                   `json:"retry_after,omitempty"`
	Context     map[string]interface{} `json:"context,omitempty"`
	OriginalErr error                  `json:"-"`
}

// Error implements the error interface
func (e *BaseKernelException) Error() string {
	return fmt.Sprintf("[%s-%d] %s", e.Layer, e.Code, e.Message)
}

// ToJSON converts exception to JSON string
func (e *BaseKernelException) ToJSON() string {
	bytes, _ := json.MarshalIndent(e, "", "  ")
	return string(bytes)
}

// ToDict converts exception to map
func (e *BaseKernelException) ToDict() map[string]interface{} {
	result := map[string]interface{}{
		"error_code":    e.Code,
		"error_message": e.Message,
		"http_code":     e.HTTPCode,
		"layer":         e.Layer,
		"severity":      e.Severity,
		"timestamp":     e.Timestamp.Format(time.RFC3339),
		"recoverable":   e.Recoverable,
	}

	if e.Details != nil && len(e.Details) > 0 {
		result["error_details"] = e.Details
	}

	if e.RetryAfter != nil {
		result["retry_after"] = *e.RetryAfter
	}

	if e.Context != nil && len(e.Context) > 0 {
		result["context"] = e.Context
	}

	return result
}

// DomainException represents domain layer exceptions (11xxxxxx)
type DomainException struct {
	*BaseKernelException
}

// NewDomainException creates a new domain exception
func NewDomainException(code int, message string, details map[string]interface{}) *DomainException {
	if code < 11000000 || code > 11999999 {
		panic(fmt.Sprintf("Domain exception code must be in range 11000000-11999999, got: %d", code))
	}

	return &DomainException{
		BaseKernelException: &BaseKernelException{
			Code:        code,
			Message:     message,
			HTTPCode:    400,
			Details:     details,
			Layer:       "domain",
			Severity:    SeverityHigh,
			Timestamp:   time.Now().UTC(),
			Recoverable: false,
			Context:     make(map[string]interface{}),
		},
	}
}

// BusinessRuleViolationException for business rule violations
type BusinessRuleViolationException struct {
	*DomainException
	RuleName string
}

// NewBusinessRuleViolationException creates a business rule violation exception
func NewBusinessRuleViolationException(message, ruleName string) *BusinessRuleViolationException {
	details := map[string]interface{}{
		"rule_violated": ruleName,
	}

	exception := NewDomainException(11001001, message, details)

	return &BusinessRuleViolationException{
		DomainException: exception,
		RuleName:        ruleName,
	}
}

// InvalidEntityStateException for invalid entity states
type InvalidEntityStateException struct {
	*DomainException
	EntityType    string
	EntityID      string
	CurrentState  string
	RequiredState string
}

// NewInvalidEntityStateException creates an invalid entity state exception
func NewInvalidEntityStateException(
	message, entityType, entityID, currentState, requiredState string,
) *InvalidEntityStateException {
	details := map[string]interface{}{
		"entity_type":    entityType,
		"entity_id":      entityID,
		"current_state":  currentState,
		"required_state": requiredState,
	}

	exception := NewDomainException(11002001, message, details)
	exception.HTTPCode = 412 // Precondition Failed

	return &InvalidEntityStateException{
		DomainException: exception,
		EntityType:      entityType,
		EntityID:        entityID,
		CurrentState:    currentState,
		RequiredState:   requiredState,
	}
}

// InvalidValueObjectException for invalid value objects
type InvalidValueObjectException struct {
	*DomainException
	ValueObjectType string
	InvalidValue    interface{}
}

// NewInvalidValueObjectException creates an invalid value object exception
func NewInvalidValueObjectException(message, valueObjectType string, invalidValue interface{}) *InvalidValueObjectException {
	details := map[string]interface{}{
		"value_object_type": valueObjectType,
		"invalid_value":     fmt.Sprintf("%v", invalidValue),
	}

	exception := NewDomainException(11003001, message, details)

	return &InvalidValueObjectException{
		DomainException: exception,
		ValueObjectType: valueObjectType,
		InvalidValue:    invalidValue,
	}
}

// DomainErrorCodes contains domain error code constants
type DomainErrorCodes struct{}

var DomainErrors = DomainErrorCodes{}

// Business Rules (11001XXX)
const (
	BusinessRuleViolation   = 11001001
	UnderageUser            = 11001002
	VehicleTooOld           = 11001003
	InvalidVehicleCapacity  = 11001004
	MaxTripDurationExceeded = 11001005
)

// Entity State (11002XXX)
const (
	InvalidEntityState      = 11002001
	UserInactive            = 11002002
	DriverNotVerified       = 11002003
	TripAlreadyCompleted    = 11002004
	BookingAlreadyCancelled = 11002005
	LicenseExpired          = 11002006
)

// Value Objects (11003XXX)
const (
	InvalidValueObject     = 11003001
	InvalidCoordinates     = 11003002
	InvalidEmailFormat     = 11003003
	InvalidPhoneFormat     = 11003004
	InvalidRatingValue     = 11003005
	CoordinatesOutOfBounds = 11003006
)

// Aggregates (11004XXX)
const (
	AggregateConsistencyViolation = 11004001
	InvalidAggregateState         = 11004002
)

// Domain Services (11005XXX)
const (
	DomainServiceError       = 11005001
	DistanceCalculationError = 11005002
	PriceCalculationError    = 11005003
)
