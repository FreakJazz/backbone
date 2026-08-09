// Package specifications provides the Specification Pattern for dynamic queries
package specifications

import "regexp"

// identifierPattern allows only safe SQL identifiers: a column name, optionally
// qualified by a table/alias ("table.column"). Anything else (whitespace,
// quotes, semicolons, SQL keywords glued onto the field, comment markers, ...)
// is rejected before it ever reaches a ToSQL() string.
var identifierPattern = regexp.MustCompile(`^[A-Za-z_][A-Za-z0-9_]*(\.[A-Za-z_][A-Za-z0-9_]*)?$`)

// isSafeIdentifier reports whether field is safe to interpolate into a SQL
// fragment. Field names cannot be parameterized with driver placeholders like
// values can, so they must be validated against an allowlist pattern instead.
func isSafeIdentifier(field string) bool {
	return identifierPattern.MatchString(field)
}

// sqlIdentifierOrFalse returns field unchanged when it is a safe identifier.
// When it is not, it returns a clause that is always false ("1=0") so an
// invalid/malicious field name can never influence the query result set or
// break out of the WHERE clause.
func sqlIdentifierOrFalse(field string) (string, bool) {
	if isSafeIdentifier(field) {
		return field, true
	}
	return "1=0", false
}
