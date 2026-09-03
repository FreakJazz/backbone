# Generates every report sonar-project.local.properties expects, then runs
# the self-hosted scanner from docker-compose.sonarqube.yml.
#
# Prereqs: SonarQube already up (docker compose -f docker-compose.sonarqube.yml
# up -d), $env:SONAR_TOKEN set (see that file's header comment), and the Go
# and Python toolchains + linters on PATH:
#   go install github.com/golangci/golangci-lint/cmd/golangci-lint@latest
#   pip install ruff bandit mypy   (or: pip install -e "backbone-python[dev]")

$ErrorActionPreference = "Stop"
Set-Location (Join-Path $PSScriptRoot "..")

if (-not $env:SONAR_TOKEN) {
    Write-Error "SONAR_TOKEN is not set - see docker-compose.sonarqube.yml's header comment."
    exit 1
}

Write-Host "==> Go: backbone-go coverage"
Push-Location backbone-go
go test ./... -coverprofile=coverage.out -covermode=atomic
Pop-Location

Write-Host "==> Go: examples/go/clean-api-go coverage"
Push-Location examples/go/clean-api-go
go test ./tests/... -coverprofile=coverage.out -covermode=atomic
Pop-Location

Write-Host "==> Go: golangci-lint (backbone-go)"
Push-Location backbone-go
golangci-lint run --out-format json | Out-File -Encoding utf8 golangci-lint-report.json
Pop-Location

Write-Host "==> Go: golangci-lint (examples/go/clean-api-go)"
Push-Location examples/go/clean-api-go
golangci-lint run --out-format json | Out-File -Encoding utf8 golangci-lint-report.json
Pop-Location

Write-Host "==> Python: backbone-python coverage"
Push-Location backbone-python
python -m pytest tests/ --cov=backbone --cov-report=xml
Pop-Location

Write-Host "==> Python: ruff"
ruff check backbone-python examples/python/clean_api_python --output-format=json | Out-File -Encoding utf8 ruff-report.json

Write-Host "==> Python: bandit"
bandit -c bandit.yaml -r backbone-python examples/python/clean_api_python -f json -o bandit-report.json

Write-Host "==> Python: mypy"
mypy backbone-python examples/python/clean_api_python | Out-File -Encoding utf8 mypy-report.txt

# golangci-lint/ruff/bandit/mypy above may exit non-zero simply because they
# found issues to report, not because they failed to run — $ErrorActionPreference
# only affects cmdlets/terminating errors, not a native exe's exit code, so
# this script keeps going either way; that's intentional, the analysis is
# the point.

Write-Host "==> SonarQube scan"
docker compose -f docker-compose.sonarqube.yml run --rm scanner

Write-Host "==> Done - see http://localhost:9000/dashboard?id=backbone-local"
