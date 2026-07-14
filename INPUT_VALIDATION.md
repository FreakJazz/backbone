# Input Validation & Error Codes

**Validación de entrada integrada al sistema de errores de backbone**

---

## The Problem

Validar entrada es común en todas las APIs. Pero la mayoría devuelven errores inconsistentes:

```
Service A:
{
  "error": "validation failed",
  "fields": ["name", "email"],
  "details": {...}
}

Service B:
{
  "status": 400,
  "message": "invalid name",
  "code": "INVALID_INPUT"
}

Service C:
{
  "errors": [
    {"field": "name", "message": "too short"},
    {"field": "email", "message": "invalid format"}
  ]
}
```

Tres servicios. Tres formatos de error de validación.

backbone resuelve esto manteniendo el **mismo contrato de error de siempre**.

---

## The Solution: Unified Validation Error

Todos los errores de validación usan la **misma estructura**:

```json
{
  "rid":         "a8866c5e750643dab7cd2a8927bbcc08",
  "status_code": 400,
  "error_code":  130000001,
  "message":     "invalid request body"
}
```

El error code `130000001` = `IFC_INVALID_REQUEST_BODY` (Interface layer validation).

**Detalles específicos de validación** van en `extra_data` (opcional):

```json
{
  "rid":         "a8866c5e750643dab7cd2a8927bbcc08",
  "status_code": 400,
  "error_code":  130000001,
  "message":     "invalid request body",
  "extra_data":  {
    "failed_fields": {
      "name":  "must be 2-50 characters",
      "email": "invalid email format",
      "price": "must be greater than 0"
    }
  }
}
```

---

## Validation Error Codes

Agregamos dos códigos al catálogo existente:

| Code        | Layer     | Name                  | HTTP |
|-------------|-----------|----------------------|------|
| `130000001` | Interface | InvalidRequestBody    | 400  |
| `130000004` | Interface | MissingRequiredParam  | 400  |

Nota: `130000005` es `InvalidFilterFormat` (ya existente para filters).

---

## Implementation in Go

### Using backbone Validators

```go
package interfaces

import (
    "encoding/json"
    "net/http"
    "regexp"
    "strings"

    "github.com/freakjazz/backbone-go/errors"
    "github.com/freakjazz/backbone-go/interfaces/responses"
    "your-app/application/commands"
)

type CreateProductRequest struct {
    Name     string  `json:"name"`
    Price    float64 `json:"price"`
    Category string  `json:"category"`
}

// Validate — built-in validation
func (r *CreateProductRequest) Validate() (map[string]string, error) {
    failed := make(map[string]string)

    // name validation
    if strings.TrimSpace(r.Name) == "" {
        failed["name"] = "name is required"
    } else if len(r.Name) < 2 || len(r.Name) > 50 {
        failed["name"] = "name must be 2-50 characters"
    }

    // price validation
    if r.Price <= 0 {
        failed["price"] = "price must be greater than 0"
    }

    // category validation
    validCategories := map[string]bool{"Electronics": true, "Furniture": true, "Books": true}
    if !validCategories[r.Category] {
        failed["category"] = "invalid category"
    }

    if len(failed) > 0 {
        return failed, nil // Validation failed, but no system error
    }

    return nil, nil // All valid
}

// HTTP Handler
func (h *ProductCommandHandler) CreateProduct(w http.ResponseWriter, r *http.Request) {
    var req CreateProductRequest
    if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
        e := responses.ErrorResponseBuilder.InvalidRequestBody(
            "malformed JSON body",
            responses.ErrorOpts{Code: errors.IfcInvalidRequestBody.Int()},
        )
        json.NewEncoder(w).Encode(e)
        return
    }

    // Validate request
    failedFields, _ := req.Validate()
    if len(failedFields) > 0 {
        e := responses.ErrorResponseBuilder.InvalidRequestBody(
            "validation failed",
            responses.ErrorOpts{
                Code: errors.IfcInvalidRequestBody.Int(),
                ExtraData: map[string]interface{}{
                    "failed_fields": failedFields,
                },
            },
        )
        json.NewEncoder(w).Encode(e)
        return
    }

    // Validation passed, proceed to use case
    cmd := commands.CreateProductCommand{
        Name:     req.Name,
        Price:    req.Price,
        Category: req.Category,
    }

    result, err := h.createCmd.Handle(r.Context(), cmd)
    if err != nil {
        // Handle application errors (conflicts, etc.)
        json.NewEncoder(w).Encode(buildErrorResponse(err))
        return
    }

    // Success
    json.NewEncoder(w).Encode(responses.ProcessResponseBuilder.Created(result.ID))
}
```

### Reusable Validators

```go
package domain

import (
    "regexp"
    "strings"
)

type Validators struct{}

func (v *Validators) ValidateEmail(email string) string {
    pattern := `^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$`
    if !regexp.MustCompile(pattern).MatchString(email) {
        return "invalid email format"
    }
    return ""
}

func (v *Validators) ValidateStringLength(value string, min, max int) string {
    length := len(strings.TrimSpace(value))
    if length < min {
        return fmt.Sprintf("must be at least %d characters", min)
    }
    if length > max {
        return fmt.Sprintf("must not exceed %d characters", max)
    }
    return ""
}

func (v *Validators) ValidatePrice(price float64) string {
    if price <= 0 {
        return "must be greater than 0"
    }
    return ""
}

func (v *Validators) ValidateEnum(value string, allowed []string) string {
    for _, a := range allowed {
        if value == a {
            return ""
        }
    }
    return fmt.Sprintf("must be one of: %s", strings.Join(allowed, ", "))
}

// Usage:
func (r *CreateProductRequest) Validate() map[string]string {
    v := &Validators{}
    failed := make(map[string]string)

    if err := v.ValidateStringLength(r.Name, 2, 50); err != "" {
        failed["name"] = err
    }

    if err := v.ValidatePrice(r.Price); err != "" {
        failed["price"] = err
    }

    return failed
}
```

---

## Implementation in Python

### Using backbone Validators

```python
from flask import Blueprint, request, jsonify
from typing import Dict, Optional
import re

from backbone import ErrorResponseBuilder, ProcessResponseBuilder
from backbone.errors import ErrorCodes
from your_app.application.commands import CreateProductCommandHandler

bp = Blueprint("products", __name__, url_prefix="/api/v1/products")

class CreateProductRequest:
    def __init__(self, data: dict):
        self.name = data.get("name", "").strip()
        self.price = data.get("price")
        self.category = data.get("category", "").strip()

    def validate(self) -> Dict[str, str]:
        """Returns dict of field -> error message if invalid, empty dict if valid."""
        failed = {}

        # name validation
        if not self.name:
            failed["name"] = "name is required"
        elif len(self.name) < 2 or len(self.name) > 50:
            failed["name"] = "name must be 2-50 characters"

        # price validation
        if self.price is None:
            failed["price"] = "price is required"
        elif not isinstance(self.price, (int, float)) or self.price <= 0:
            failed["price"] = "price must be greater than 0"

        # category validation
        valid_categories = ["Electronics", "Furniture", "Books"]
        if self.category not in valid_categories:
            failed["category"] = f"invalid category, must be one of: {', '.join(valid_categories)}"

        return failed

@bp.route("", methods=["POST"])
def create_product():
    try:
        data = request.get_json()
        if not data:
            err = ErrorResponseBuilder.invalid_request_body(
                "malformed JSON body",
                error_code=ErrorCodes.IFC_INVALID_REQUEST_BODY
            )
            return jsonify(err), 400

        # Parse request
        req = CreateProductRequest(data)

        # Validate
        failed_fields = req.validate()
        if failed_fields:
            err = ErrorResponseBuilder.invalid_request_body(
                "validation failed",
                error_code=ErrorCodes.IFC_INVALID_REQUEST_BODY,
                extra_data={"failed_fields": failed_fields}
            )
            return jsonify(err), 400

        # Validation passed, proceed to use case
        from your_app.application.commands import CreateProductCommand
        cmd = CreateProductCommand(
            name=req.name,
            price=req.price,
            category=req.category
        )

        handler = CreateProductCommandHandler(repo)
        result = handler.handle(cmd)

        return jsonify(ProcessResponseBuilder.created(result.id)), 201

    except Exception as e:
        # Handle other errors
        err = ErrorResponseBuilder.internal_error(str(e))
        return jsonify(err), 500
```

### Reusable Validators

```python
import re
from typing import Optional

class Validators:
    @staticmethod
    def validate_email(email: str) -> Optional[str]:
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(pattern, email):
            return "invalid email format"
        return None

    @staticmethod
    def validate_string_length(value: str, min_len: int, max_len: int) -> Optional[str]:
        length = len(value.strip())
        if length < min_len:
            return f"must be at least {min_len} characters"
        if length > max_len:
            return f"must not exceed {max_len} characters"
        return None

    @staticmethod
    def validate_price(price: float) -> Optional[str]:
        if price <= 0:
            return "must be greater than 0"
        return None

    @staticmethod
    def validate_enum(value: str, allowed: list) -> Optional[str]:
        if value not in allowed:
            return f"must be one of: {', '.join(allowed)}"
        return None

    @staticmethod
    def validate_url(url: str) -> Optional[str]:
        pattern = r'^https?://'
        if not re.match(pattern, url):
            return "must be a valid HTTP(S) URL"
        return None

# Usage:
class CreateProductRequest:
    def validate(self) -> Dict[str, str]:
        v = Validators()
        failed = {}

        if err := v.validate_string_length(self.name, 2, 50):
            failed["name"] = err

        if err := v.validate_price(self.price):
            failed["price"] = err

        return failed
```

---

## Client-Side Handling

El cliente siempre recibe la misma estructura:

```javascript
// JavaScript/TypeScript
async function createProduct(data) {
    const response = await fetch('/api/v1/products', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
    });

    const json = await response.json();

    if (!response.ok) {
        // Error response
        const { error_code, message, extra_data } = json;

        if (error_code === 130000001) {  // IFC_INVALID_REQUEST_BODY
            // Show validation errors
            if (extra_data?.failed_fields) {
                for (const [field, error] of Object.entries(extra_data.failed_fields)) {
                    console.error(`${field}: ${error}`);
                }
            }
        }

        return { success: false, error: message };
    }

    return { success: true, id: json.id };
}

// Usage:
const result = await createProduct({ name: "", price: -100 });
// Error: 
// name: must be 2-50 characters
// price: must be greater than 0
```

---

## Testing Validation

### Go

```go
func TestCreateProductRequest_InvalidName(t *testing.T) {
    req := &CreateProductRequest{
        Name:     "", // Invalid
        Price:    100.0,
        Category: "Electronics",
    }

    failed := req.Validate()

    if _, hasName := failed["name"]; !hasName {
        t.Error("expected name validation error")
    }
    if _, hasPrice := failed["price"]; hasPrice {
        t.Error("price should be valid")
    }
}

func TestCreateProductHandler_ValidateFails(t *testing.T) {
    payload := map[string]interface{}{
        "name":     "", // Empty
        "price":    -50.0, // Negative
        "category": "Unknown",
    }

    body, _ := json.Marshal(payload)
    req := httptest.NewRequest("POST", "/products", bytes.NewBuffer(body))
    w := httptest.NewRecorder()

    handler.CreateProduct(w, req)

    if w.Code != http.StatusBadRequest {
        t.Errorf("expected 400, got %d", w.Code)
    }

    var response map[string]interface{}
    json.Unmarshal(w.Body.Bytes(), &response)

    // Assert error code
    if int(response["error_code"].(float64)) != errors.IfcInvalidRequestBody.Int() {
        t.Error("expected IFC_INVALID_REQUEST_BODY")
    }

    // Assert failed fields
    if extraData, ok := response["extra_data"]; ok {
        if failedFields, ok := extraData.(map[string]interface{})["failed_fields"]; ok {
            failed := failedFields.(map[string]interface{})
            if _, hasName := failed["name"]; !hasName {
                t.Error("expected name in failed_fields")
            }
        }
    }
}
```

### Python

```python
import pytest

class TestCreateProductRequest:
    def test_invalid_name(self):
        req = CreateProductRequest({"name": "", "price": 100.0, "category": "Electronics"})
        failed = req.validate()
        
        assert "name" in failed
        assert "price" not in failed

    def test_multiple_validation_errors(self):
        req = CreateProductRequest({"name": "", "price": -50.0, "category": "Unknown"})
        failed = req.validate()
        
        assert "name" in failed
        assert "price" in failed
        assert "category" in failed

class TestCreateProductHandler:
    def test_validation_fails(self, client):
        response = client.post(
            "/api/v1/products",
            json={"name": "", "price": -50.0, "category": "Unknown"}
        )
        
        assert response.status_code == 400
        data = response.get_json()
        
        assert data["error_code"] == ErrorCodes.IFC_INVALID_REQUEST_BODY
        assert "failed_fields" in data.get("extra_data", {})
        assert "name" in data["extra_data"]["failed_fields"]
```

---

## Summary Table

| Aspect | Implementation |
|--------|-----------------|
| **Error Code** | `130000001` (IFC_INVALID_REQUEST_BODY) |
| **HTTP Status** | `400` (Bad Request) |
| **Response Structure** | Same 4-field contract (rid, status_code, error_code, message) |
| **Field Errors** | In `extra_data.failed_fields` (optional) |
| **Validators** | Reusable, testable, simple |
| **Testing** | Easy with mock repositories |

---

**Input validation es parte del framework, no una versión nueva. Es simplemente cómo manejas los errores `130000001` en tu Interface layer.**
