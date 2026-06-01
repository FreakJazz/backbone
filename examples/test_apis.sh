#!/bin/bash

# 🧪 Script de Testing - Clean API Examples

echo "🧪 Testing Clean API Examples"
echo "=============================="
echo ""

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Función para hacer request y mostrar resultado
test_request() {
    local name=$1
    local method=$2
    local url=$3
    local data=$4
    
    echo -e "${BLUE}Testing: $name${NC}"
    
    if [ -z "$data" ]; then
        response=$(curl -s -w "\n%{http_code}" -X $method "$url")
    else
        response=$(curl -s -w "\n%{http_code}" -X $method -H "Content-Type: application/json" -d "$data" "$url")
    fi
    
    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | sed '$d')
    
    if [ "$http_code" -ge 200 ] && [ "$http_code" -lt 300 ]; then
        echo -e "${GREEN}✅ $http_code - Success${NC}"
        echo "$body" | python3 -m json.tool 2>/dev/null || echo "$body"
    else
        echo -e "${RED}❌ $http_code - Failed${NC}"
        echo "$body"
    fi
    
    echo ""
}

# Verificar si las APIs están corriendo
echo "Verificando APIs..."
echo ""

GO_RUNNING=false
PYTHON_RUNNING=false

if curl -s http://localhost:8080/health > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Go API está corriendo (puerto 8080)${NC}"
    GO_RUNNING=true
else
    echo -e "${YELLOW}⚠️  Go API no está corriendo (puerto 8080)${NC}"
fi

if curl -s http://localhost:5000/health > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Python API está corriendo (puerto 5000)${NC}"
    PYTHON_RUNNING=true
else
    echo -e "${YELLOW}⚠️  Python API no está corriendo (puerto 5000)${NC}"
fi

echo ""
echo "=============================="
echo ""

# Test Go API
if [ "$GO_RUNNING" = true ]; then
    echo -e "${BLUE}═══ Testing Go API (port 8080) ═══${NC}"
    echo ""
    
    # Health check
    test_request "Health Check" "GET" "http://localhost:8080/health"
    
    # Create product
    test_request "Create Product" "POST" "http://localhost:8080/api/products" '{
        "name": "Test Product Go",
        "description": "A test product from Go API",
        "price": 999.99,
        "category": "Testing",
        "stock": 100
    }'
    
    # Get all products
    test_request "Get All Products" "GET" "http://localhost:8080/api/products"
    
    # Get with filters
    test_request "Get Electronics with Price Range" "GET" "http://localhost:8080/api/products?category=Electronics&min_price=1000&max_price=2000"
    
    # Get with pagination
    test_request "Get Products (page 1, size 2)" "GET" "http://localhost:8080/api/products?page=1&page_size=2"
    
    echo ""
fi

# Test Python API
if [ "$PYTHON_RUNNING" = true ]; then
    echo -e "${BLUE}═══ Testing Python API (port 5000) ═══${NC}"
    echo ""
    
    # Health check
    test_request "Health Check" "GET" "http://localhost:5000/health"
    
    # Create product
    test_request "Create Product" "POST" "http://localhost:5000/api/products" '{
        "name": "Test Product Python",
        "description": "A test product from Python API",
        "price": 888.88,
        "category": "Testing",
        "stock": 50
    }'
    
    # Get all products
    test_request "Get All Products" "GET" "http://localhost:5000/api/products"
    
    # Get with filters
    test_request "Get Electronics with Price Range" "GET" "http://localhost:5000/api/products?category=Electronics&min_price=1000&max_price=2000"
    
    # Get with pagination
    test_request "Get Products (page 1, size 2)" "GET" "http://localhost:5000/api/products?page=1&page_size=2"
    
    # Get with in_stock filter
    test_request "Get In-Stock Products" "GET" "http://localhost:5000/api/products?in_stock=true"
    
    echo ""
fi

echo "=============================="
echo -e "${GREEN}✅ Testing completed!${NC}"
echo ""
