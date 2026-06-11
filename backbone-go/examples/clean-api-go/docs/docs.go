// Package docs — Swagger 2.0 spec (manually maintained — swag not available in this env).
package docs

import "github.com/swaggo/swag"

const docTemplate = `{
    "swagger": "2.0",
    "info": {
        "title":       "{{.Title}}",
        "description": "{{escape .Description}}",
        "version":     "{{.Version}}",
        "license":     {"name": "MIT"}
    },
    "host":     "{{.Host}}",
    "basePath": "{{.BasePath}}",
    "schemes":  {{ marshal .Schemes }},
    "consumes": ["application/json"],
    "produces": ["application/json"],

    "paths": {

        "/v1/products": {

            "get": {
                "tags":    ["products"],
                "summary": "List products with dynamic filters",
                "description": "CQRS query. Filter examples:\n  ?filters=category,eq,Electronics,and\\u0026filters=price,gt,500\n  ?filters=name,contains,laptop\\u0026sort_by=price:asc\n  ?filters=price,between,100|2000\\u0026page=2\\u0026page_size=5",
                "parameters": [
                    {"name":"filters",   "in":"query","type":"array","collectionFormat":"multi","items":{"type":"string"},"description":"Repeated. Format: field,operator,value[,condition]. Operators: eq ne gt gte lt lte contains in between is_null is_not_null. Example: filters=category,eq,Electronics,and"},
                    {"name":"page",      "in":"query","type":"integer","default":1,  "description":"Page number"},
                    {"name":"page_size", "in":"query","type":"integer","default":10, "description":"Items per page"},
                    {"name":"sort_by",   "in":"query","type":"string",               "description":"field:direction — e.g. price:desc (default created_at:desc)"}
                ],
                "responses": {
                    "200": {"description":"OK",           "schema":{"$ref":"#/definitions/PaginatedResponse"}},
                    "500": {"description":"Server error", "schema":{"$ref":"#/definitions/ErrorResponse"}}
                }
            },

            "post": {
                "tags":    ["products"],
                "summary": "Create a new product",
                "description": "CQRS command. Returns {\"id\": \"uuid\"}.",
                "parameters": [
                    {"name":"body","in":"body","required":true,"schema":{"$ref":"#/definitions/CreateProductRequest"}}
                ],
                "responses": {
                    "201": {"description":"Created",          "schema":{"$ref":"#/definitions/IDResponse"}},
                    "400": {"description":"Validation error", "schema":{"$ref":"#/definitions/ErrorResponse"}}
                }
            }
        },

        "/v1/products/{id}": {

            "get": {
                "tags":    ["products"],
                "summary": "Get a product by ID",
                "description": "CQRS query. Returns the raw product object without envelope.",
                "parameters": [
                    {"name":"id","in":"path","required":true,"type":"string","description":"Product ID"}
                ],
                "responses": {
                    "200": {"description":"OK",        "schema":{"$ref":"#/definitions/Product"}},
                    "404": {"description":"Not found", "schema":{"$ref":"#/definitions/ErrorResponse"}}
                }
            },

            "put": {
                "tags":    ["products"],
                "summary": "Update a product",
                "description": "CQRS command. Returns {\"id\": \"uuid\"}.",
                "parameters": [
                    {"name":"id",  "in":"path","required":true,"type":"string","description":"Product ID"},
                    {"name":"body","in":"body","required":true,"schema":{"$ref":"#/definitions/UpdateProductRequest"}}
                ],
                "responses": {
                    "200": {"description":"Updated",          "schema":{"$ref":"#/definitions/IDResponse"}},
                    "400": {"description":"Validation error", "schema":{"$ref":"#/definitions/ErrorResponse"}},
                    "404": {"description":"Not found",        "schema":{"$ref":"#/definitions/ErrorResponse"}}
                }
            },

            "delete": {
                "tags":    ["products"],
                "summary": "Delete a product",
                "description": "CQRS command. Returns {\"id\": \"uuid\"}.",
                "parameters": [
                    {"name":"id","in":"path","required":true,"type":"string","description":"Product ID"}
                ],
                "responses": {
                    "200": {"description":"Deleted",   "schema":{"$ref":"#/definitions/IDResponse"}},
                    "404": {"description":"Not found", "schema":{"$ref":"#/definitions/ErrorResponse"}}
                }
            }
        },

        "/v1/products/{id}/status": {

            "patch": {
                "tags":    ["products"],
                "summary": "Activate or deactivate a product",
                "description": "CQRS command. Returns {\"id\": \"uuid\"}.",
                "parameters": [
                    {"name":"id",  "in":"path","required":true,"type":"string","description":"Product ID"},
                    {"name":"body","in":"body","required":true,"schema":{"$ref":"#/definitions/ChangeStatusRequest"}}
                ],
                "responses": {
                    "200": {"description":"Updated",   "schema":{"$ref":"#/definitions/IDResponse"}},
                    "404": {"description":"Not found", "schema":{"$ref":"#/definitions/ErrorResponse"}}
                }
            }
        }
    },

    "definitions": {

        "IDResponse": {
            "type": "object",
            "properties": {
                "id": {"type":"string","example":"uuid-123"}
            }
        },

        "Product": {
            "type": "object",
            "properties": {
                "id":          {"type":"string"},
                "name":        {"type":"string"},
                "description": {"type":"string"},
                "price":       {"type":"number"},
                "category":    {"type":"string"},
                "stock":       {"type":"integer"},
                "active":      {"type":"boolean"},
                "created_at":  {"type":"string","format":"date-time"},
                "updated_at":  {"type":"string","format":"date-time"}
            }
        },

        "PaginatedMeta": {
            "type": "object",
            "properties": {
                "status":      {"type":"string","example":"success"},
                "status_code": {"type":"integer","example":200},
                "message":     {"type":"string"}
            }
        },

        "Pagination": {
            "type": "object",
            "properties": {
                "total_count": {"type":"integer"},
                "page":        {"type":"integer"},
                "page_size":   {"type":"integer"}
            }
        },

        "PaginatedResponse": {
            "type": "object",
            "properties": {
                "meta":       {"$ref":"#/definitions/PaginatedMeta"},
                "items":      {"type":"array","items":{"$ref":"#/definitions/Product"}},
                "pagination": {"$ref":"#/definitions/Pagination"}
            }
        },

        "ErrorResponse": {
            "type": "object",
            "properties": {
                "request_id":  {"type":"string"},
                "status_code": {"type":"integer"},
                "message":     {"type":"string"},
                "code_error":  {"type":"string"},
                "field_errors":{"type":"object","additionalProperties":{"type":"string"}}
            }
        },

        "CreateProductRequest": {
            "type": "object",
            "required": ["name","price","category","stock"],
            "properties": {
                "name":        {"type":"string", "example":"Laptop Dell XPS 15"},
                "description": {"type":"string", "example":"High performance laptop"},
                "price":       {"type":"number", "example":1500.00},
                "category":    {"type":"string", "example":"Electronics"},
                "stock":       {"type":"integer","example":50}
            }
        },

        "UpdateProductRequest": {
            "type": "object",
            "properties": {
                "name":        {"type":"string", "example":"Laptop Dell XPS 15 Updated"},
                "description": {"type":"string", "example":"Updated description"},
                "price":       {"type":"number", "example":1400.00},
                "category":    {"type":"string", "example":"Electronics"},
                "stock":       {"type":"integer","example":45}
            }
        },

        "ChangeStatusRequest": {
            "type": "object",
            "required": ["active"],
            "properties": {
                "active": {"type":"boolean","example":false}
            }
        }
    }
}`

// SwaggerInfo holds exported Swagger Info so clients can modify it.
var SwaggerInfo = &swag.Spec{
	Version:          "1.0",
	Host:             "localhost:8080",
	BasePath:         "/api",
	Schemes:          []string{"http"},
	Title:            "Product API — Clean Architecture + CQRS",
	Description:      "backbone-go example: full CRUD with Clean Architecture and CQRS pattern",
	InfoInstanceName: "swagger",
	SwaggerTemplate:  docTemplate,
	LeftDelim:        "{{",
	RightDelim:       "}}",
}

func init() {
	swag.Register(SwaggerInfo.InstanceName(), SwaggerInfo)
}
