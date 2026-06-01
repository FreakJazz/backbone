# 🧪 Testing APIs - PowerShell Script

Write-Host "🧪 Testing Clean API Examples" -ForegroundColor Cyan
Write-Host "==============================" -ForegroundColor Cyan
Write-Host ""

function Test-Request {
    param(
        [string]$Name,
        [string]$Method,
        [string]$Url,
        [string]$Data = $null
    )
    
    Write-Host "Testing: $Name" -ForegroundColor Blue
    
    try {
        if ($Data) {
            $response = Invoke-RestMethod -Uri $Url -Method $Method -Body $Data -ContentType "application/json" -ErrorAction Stop
        } else {
            $response = Invoke-RestMethod -Uri $Url -Method $Method -ErrorAction Stop
        }
        
        Write-Host "✅ Success" -ForegroundColor Green
        $response | ConvertTo-Json -Depth 10
    } catch {
        Write-Host "❌ Failed: $($_.Exception.Message)" -ForegroundColor Red
    }
    
    Write-Host ""
}

# Check if APIs are running
Write-Host "Checking APIs..." -ForegroundColor Yellow
Write-Host ""

$goRunning = $false
$pythonRunning = $false

try {
    Invoke-RestMethod -Uri "http://localhost:8080/health" -ErrorAction Stop | Out-Null
    Write-Host "✅ Go API is running (port 8080)" -ForegroundColor Green
    $goRunning = $true
} catch {
    Write-Host "⚠️  Go API is not running (port 8080)" -ForegroundColor Yellow
}

try {
    Invoke-RestMethod -Uri "http://localhost:5000/health" -ErrorAction Stop | Out-Null
    Write-Host "✅ Python API is running (port 5000)" -ForegroundColor Green
    $pythonRunning = $true
} catch {
    Write-Host "⚠️  Python API is not running (port 5000)" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "==============================" -ForegroundColor Cyan
Write-Host ""

# Test Go API
if ($goRunning) {
    Write-Host "═══ Testing Go API (port 8080) ═══" -ForegroundColor Cyan
    Write-Host ""
    
    Test-Request "Health Check" "GET" "http://localhost:8080/health"
    
    Test-Request "Create Product" "POST" "http://localhost:8080/api/products" @"
{
    "name": "Test Product Go",
    "description": "A test product from Go API",
    "price": 999.99,
    "category": "Testing",
    "stock": 100
}
"@
    
    Test-Request "Get All Products" "GET" "http://localhost:8080/api/products"
    
    Test-Request "Get Electronics with Price Range" "GET" "http://localhost:8080/api/products?category=Electronics&min_price=1000&max_price=2000"
    
    Test-Request "Get Products (page 1, size 2)" "GET" "http://localhost:8080/api/products?page=1&page_size=2"
    
    Write-Host ""
}

# Test Python API
if ($pythonRunning) {
    Write-Host "═══ Testing Python API (port 5000) ═══" -ForegroundColor Cyan
    Write-Host ""
    
    Test-Request "Health Check" "GET" "http://localhost:5000/health"
    
    Test-Request "Create Product" "POST" "http://localhost:5000/api/products" @"
{
    "name": "Test Product Python",
    "description": "A test product from Python API",
    "price": 888.88,
    "category": "Testing",
    "stock": 50
}
"@
    
    Test-Request "Get All Products" "GET" "http://localhost:5000/api/products"
    
    Test-Request "Get Electronics with Price Range" "GET" "http://localhost:5000/api/products?category=Electronics&min_price=1000&max_price=2000"
    
    Test-Request "Get Products (page 1, size 2)" "GET" "http://localhost:5000/api/products?page=1&page_size=2"
    
    Test-Request "Get In-Stock Products" "GET" "http://localhost:5000/api/products?in_stock=true"
    
    Write-Host ""
}

Write-Host "==============================" -ForegroundColor Cyan
Write-Host "✅ Testing completed!" -ForegroundColor Green
Write-Host ""
