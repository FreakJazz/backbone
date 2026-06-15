package handlers

// ErrorResponse mirrors the backbone-go error contract for Swagger documentation.
type ErrorResponse struct {
	RID        string `json:"rid"         example:"afdef44d-2f09-49d8-a847-89e0c56d8ce4"`
	StatusCode int    `json:"status_code" example:"400"`
	Message    string `json:"message"     example:"name must be at least 2 characters"`
	ErrorCode  int    `json:"error_code"  example:"130000001"`
}
