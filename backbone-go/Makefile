# Makefile for Backbone-Go

.PHONY: help build test test-coverage test-verbose clean run example lint fmt vet install deps

# Variables
BINARY_NAME=backbone-example
GO=go
GOTEST=$(GO) test
GOVET=$(GO) vet
GOFMT=gofmt
GOLINT=golangci-lint

help: ## Show this help
	@echo "Available targets:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

deps: ## Install dependencies
	@echo "Installing dependencies..."
	$(GO) mod download
	$(GO) mod tidy

install: deps ## Install the package
	@echo "Installing backbone-go..."
	$(GO) install

build: ## Build the example application
	@echo "Building $(BINARY_NAME)..."
	$(GO) build -o bin/$(BINARY_NAME) ./examples/basic/main.go

run: ## Run the example application
	@echo "Running example..."
	$(GO) run ./examples/basic/main.go

example: build ## Build and run the example
	@echo "Running built example..."
	./bin/$(BINARY_NAME)

test: ## Run all tests
	@echo "Running tests..."
	$(GOTEST) -v ./...

test-coverage: ## Run tests with coverage
	@echo "Running tests with coverage..."
	$(GOTEST) -cover -coverprofile=coverage.out ./...
	$(GO) tool cover -html=coverage.out -o coverage.html
	@echo "Coverage report generated: coverage.html"

test-verbose: ## Run tests with verbose output
	@echo "Running tests (verbose)..."
	$(GOTEST) -v -race ./...

test-unit: ## Run only unit tests
	@echo "Running unit tests..."
	$(GOTEST) -short -v ./...

bench: ## Run benchmarks
	@echo "Running benchmarks..."
	$(GOTEST) -bench=. -benchmem ./...

lint: ## Run linter
	@echo "Running linter..."
	$(GOLINT) run ./...

fmt: ## Format code
	@echo "Formatting code..."
	$(GOFMT) -s -w .

vet: ## Run go vet
	@echo "Running go vet..."
	$(GOVET) ./...

clean: ## Clean build artifacts
	@echo "Cleaning..."
	rm -rf bin/
	rm -rf event_store/
	rm -f coverage.out coverage.html
	$(GO) clean

check: fmt vet lint test ## Run all checks (format, vet, lint, test)

ci: deps check ## Run CI pipeline

# Development helpers
dev-setup: ## Setup development environment
	@echo "Setting up development environment..."
	$(GO) install github.com/golangci/golangci-lint/cmd/golangci-lint@latest
	$(GO) install github.com/stretchr/testify@latest
	@echo "Development environment ready!"

watch: ## Watch for changes and run tests
	@echo "Watching for changes..."
	@which watchexec > /dev/null || (echo "Install watchexec: https://github.com/watchexec/watchexec" && exit 1)
	watchexec -e go -r "make test"

# Docker
docker-build: ## Build Docker image
	@echo "Building Docker image..."
	docker build -t backbone-go:latest .

docker-run: ## Run Docker container
	@echo "Running Docker container..."
	docker run -p 8000:8000 backbone-go:latest

# Documentation
docs: ## Generate documentation
	@echo "Generating documentation..."
	godoc -http=:6060 &
	@echo "Documentation server running at http://localhost:6060"

# Release
release: clean test ## Prepare release
	@echo "Preparing release..."
	@echo "Don't forget to:"
	@echo "  1. Update version in README.md"
	@echo "  2. Update CHANGELOG.md"
	@echo "  3. Create git tag: git tag -a vX.Y.Z -m 'Release vX.Y.Z'"
	@echo "  4. Push tag: git push origin vX.Y.Z"
