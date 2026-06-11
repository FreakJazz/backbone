#!/bin/bash

# 🎯 Script de Demostración - Clean API Examples

echo "🚀 Clean API Examples - Go vs Python"
echo "======================================"
echo ""

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}Este script ejecuta las APIs de Go y Python simultáneamente${NC}"
echo ""

# Función para matar procesos al salir
cleanup() {
    echo ""
    echo -e "${YELLOW}Deteniendo servidores...${NC}"
    kill $GO_PID 2>/dev/null
    kill $PYTHON_PID 2>/dev/null
    echo "✅ Servidores detenidos"
    exit 0
}

trap cleanup INT TERM

# Verificar si Go está instalado
if ! command -v go &> /dev/null; then
    echo -e "${YELLOW}⚠️  Go no está instalado. Saltando ejemplo de Go.${NC}"
    GO_AVAILABLE=false
else
    GO_AVAILABLE=true
fi

# Verificar si Python está instalado
if ! command -v python3 &> /dev/null; then
    echo -e "${YELLOW}⚠️  Python no está instalado. Saltando ejemplo de Python.${NC}"
    PYTHON_AVAILABLE=false
else
    PYTHON_AVAILABLE=true
fi

# Iniciar Go API
if [ "$GO_AVAILABLE" = true ]; then
    echo -e "${BLUE}▶️  Iniciando Go API (puerto 8080)...${NC}"
    cd examples/clean-api-go
    go run main.go &> go.log &
    GO_PID=$!
    cd ../..
    sleep 2
    
    # Verificar si está corriendo
    if curl -s http://localhost:8080/health > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Go API corriendo en http://localhost:8080${NC}"
    else
        echo -e "${YELLOW}⚠️  Go API no está respondiendo${NC}"
    fi
    echo ""
fi

# Iniciar Python API
if [ "$PYTHON_AVAILABLE" = true ]; then
    echo -e "${BLUE}▶️  Iniciando Python API (puerto 5000)...${NC}"
    cd examples/clean_api_python
    pip install -r requirements.txt > /dev/null 2>&1
    python3 main.py &> python.log &
    PYTHON_PID=$!
    cd ../..
    sleep 3
    
    # Verificar si está corriendo
    if curl -s http://localhost:5000/health > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Python API corriendo en http://localhost:5000${NC}"
    else
        echo -e "${YELLOW}⚠️  Python API no está respondiendo${NC}"
    fi
    echo ""
fi

echo "======================================"
echo -e "${GREEN}📝 APIs disponibles:${NC}"
echo ""

if [ "$GO_AVAILABLE" = true ]; then
    echo -e "${BLUE}Go API:${NC}"
    echo "  http://localhost:8080/api/products"
    echo "  http://localhost:8080/health"
    echo ""
fi

if [ "$PYTHON_AVAILABLE" = true ]; then
    echo -e "${BLUE}Python API:${NC}"
    echo "  http://localhost:5000/api/products"
    echo "  http://localhost:5000/health"
    echo ""
fi

echo "======================================"
echo -e "${YELLOW}💡 Ejecuta ./examples/test_apis.sh para probar las APIs${NC}"
echo -e "${YELLOW}💡 Presiona Ctrl+C para detener los servidores${NC}"
echo ""

# Mantener el script corriendo
wait
