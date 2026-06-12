// Package errors provides structured error codes for the backbone framework.
//
// Code format: LL_NNNNNNN  (9 digits total)
//
//	LL      = 2-digit layer prefix (11–14)
//	NNNNNNN = 7-digit sequence within the layer (0000001–9999999)
//
// Examples:
//
//	110000001 → Domain layer, error #1
//	120000042 → Application layer, error #42
//	130000007 → Interface layer, error #7
//	140000015 → Infrastructure layer, error #15
package errors

import "fmt"

// Layer prefixes — define which architectural layer owns the error.
const (
	LayerDomain         = 11 // Business rules, entities, value objects, aggregates
	LayerApplication    = 12 // Use cases, commands, queries, application services
	LayerInterface      = 13 // HTTP handlers, gRPC adapters, CLI, WebSocket
	LayerInfrastructure = 14 // Databases, messaging brokers, external APIs, cache
)

// ErrorCode is a 9-digit structured code: LL_NNNNNNN.
// Use New() to construct; the zero value is invalid.
type ErrorCode int

// New returns an ErrorCode for the given layer and number.
// Returns 0 (invalid) if either argument is out of range — never panics.
//
//	layer  : 11–19
//	number : 1–9_999_999
func New(layer, number int) ErrorCode {
	if layer < 11 || layer > 19 {
		return 0
	}
	if number < 1 || number > 9_999_999 {
		return 0
	}
	return ErrorCode(layer*10_000_000 + number)
}

// Parse reconstructs an ErrorCode from a raw integer.
// Returns 0 if the value does not conform to the LL_NNNNNNN format.
func Parse(v int) ErrorCode {
	c := ErrorCode(v)
	if !c.Valid() {
		return 0
	}
	return c
}

// Layer returns the 2-digit layer prefix (11–14).
func (c ErrorCode) Layer() int { return int(c) / 10_000_000 }

// Number returns the 7-digit sequence within the layer.
func (c ErrorCode) Number() int { return int(c) % 10_000_000 }

// Valid reports whether the code has a legal layer prefix and a non-zero number.
func (c ErrorCode) Valid() bool {
	l := c.Layer()
	return l >= 11 && l <= 19 && c.Number() >= 1
}

// Int returns the raw integer value — use when embedding in JSON or error builders.
func (c ErrorCode) Int() int { return int(c) }

// String formats the code as a 9-digit string, e.g. "110000023".
func (c ErrorCode) String() string { return fmt.Sprintf("%d", int(c)) }

// LayerName returns a human-readable label for the layer prefix.
func (c ErrorCode) LayerName() string {
	switch c.Layer() {
	case LayerDomain:
		return "domain"
	case LayerApplication:
		return "application"
	case LayerInterface:
		return "interface"
	case LayerInfrastructure:
		return "infrastructure"
	default:
		return "unknown"
	}
}

// ── Catálogo de códigos backbone ──────────────────────────────────────────────
//
// Cada capa tiene su propio rango numérico secuencial empezando en 0000001.
// Los sistemas que usen backbone pueden extender el catálogo con sus propios
// códigos siguiendo la misma convención: New(LayerXxx, N).
//
// Tabla de capas:
//
//	11 = Domain        → reglas de negocio, entidades, value objects
//	12 = Application   → casos de uso, commands, queries, servicios de aplicación
//	13 = Interface     → handlers HTTP, adaptadores gRPC, CLI
//	14 = Infrastructure→ bases de datos, mensajería, servicios externos, caché
//
// Formato del código: LL_NNNNNNN  (9 dígitos)
//
//	11_0000001 = 110000001   Domain, error #1
//	12_0000001 = 120000001   Application, error #1
//	13_0000001 = 130000001   Interface, error #1
//	14_0000001 = 140000001   Infrastructure, error #1

var (
	// ── Domain (11) ──────────────────────────────────────────────────────────
	DomainBusinessRuleViolation  = New(LayerDomain, 1) // 110000001
	DomainInvalidEntityState     = New(LayerDomain, 2) // 110000002
	DomainInvalidValueObject     = New(LayerDomain, 3) // 110000003
	DomainAggregateInconsistency = New(LayerDomain, 4) // 110000004
	DomainInvalidFilter          = New(LayerDomain, 5) // 110000005

	// ── Application (12) ─────────────────────────────────────────────────────
	AppUseCaseFailure         = New(LayerApplication, 1) // 120000001
	AppValidationFailure      = New(LayerApplication, 2) // 120000002
	AppAuthorizationDenied    = New(LayerApplication, 3) // 120000003
	AppResourceNotFound       = New(LayerApplication, 4) // 120000004
	AppExternalServiceFailure = New(LayerApplication, 5) // 120000005
	AppConflict               = New(LayerApplication, 6) // 120000006

	// ── Interface / HTTP (13) ────────────────────────────────────────────────
	IfcInvalidRequestBody   = New(LayerInterface, 1) // 130000001
	IfcMethodNotAllowed     = New(LayerInterface, 2) // 130000002
	IfcRouteNotFound        = New(LayerInterface, 3) // 130000003
	IfcMissingRequiredParam = New(LayerInterface, 4) // 130000004
	IfcInvalidFilterFormat  = New(LayerInterface, 5) // 130000005
	IfcUnauthorized         = New(LayerInterface, 6) // 130000006
	IfcForbidden            = New(LayerInterface, 7) // 130000007

	// ── Infrastructure (14) ──────────────────────────────────────────────────
	InfraDBFailure          = New(LayerInfrastructure, 1) // 140000001
	InfraMessagingFailure   = New(LayerInfrastructure, 2) // 140000002
	InfraCacheFailure       = New(LayerInfrastructure, 3) // 140000003
	InfraExternalAPIFailure = New(LayerInfrastructure, 4) // 140000004
	InfraServiceUnavailable = New(LayerInfrastructure, 5) // 140000005
)
