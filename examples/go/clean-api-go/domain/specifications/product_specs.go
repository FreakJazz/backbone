package specifications

import (
	"github.com/freakjazz/backbone-go/domain/specifications"
)

var ValidSortFields = map[string]bool{
	"name": true, "price": true, "category": true, "status": true,
}

func BuildCriteria(filters []string, page, pageSize int, sortBy string) *specifications.Criteria {
	sortField, sortDir := specifications.ParseSortBy(sortBy)
	if !ValidSortFields[sortField] {
		sortField = "name"
		sortDir = "asc"
	}
	return specifications.ParseFilterParams(filters, page, pageSize, sortField, sortDir)
}
