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

# `go test ./... -coverprofile=...` produces no file at all here: both Go
# modules' tests live in external test packages under tests/ (exercising
# the library through its public API, not from inside each package), so
# `./...` also matches every production package directory, which has no
# _test.go files of its own — go test never merges a coverage profile in
# that mixed shape (verified: silently no coverage.out, no error). Scoping
# the *test target* to ./tests/... while using -coverpkg=./... to still
# instrument (and attribute coverage to) the production packages is what
# actually produces a valid, non-empty profile.
Write-Host "==> Go: backbone-go coverage"
Push-Location backbone-go
& go test "./tests/..." "-coverpkg=./..." "-coverprofile=coverage.out" "-covermode=atomic"
Pop-Location

Write-Host "==> Go: examples/go/clean-api-go coverage"
Push-Location examples/go/clean-api-go
& go test "./tests/..." "-coverpkg=./..." "-coverprofile=coverage.out" "-covermode=atomic"
Pop-Location

Write-Host "==> Go: golangci-lint (backbone-go)"
Push-Location backbone-go
golangci-lint run --out-format json | Out-File -Encoding utf8 golangci-lint-report.json
Pop-Location

Write-Host "==> Go: golangci-lint (examples/go/clean-api-go)"
Push-Location examples/go/clean-api-go
golangci-lint run --out-format json | Out-File -Encoding utf8 golangci-lint-report.json
Pop-Location

# Run from the repo root (not `cd backbone-python; pytest tests/`) so
# coverage.py's `relative_files = true` (pyproject.toml) records paths
# relative to the repo root ("backbone-python/domain/...") — matching what
# sonar.sources expects. Run from inside backbone-python instead and the
# same setting records paths relative to *that* directory ("domain/...",
# "conftest.py"), which the scanner then can't resolve at all (verified:
# every file's coverage measure silently dropped, "Cannot resolve the file
# path 'conftest.py'"). --cov-config is explicit because coverage.py's own
# config auto-discovery looks in the current directory (the repo root here,
# which has no [tool.coverage] section of its own).
Write-Host "==> Python: backbone-python coverage"
python -m pytest backbone-python/tests --cov=backbone --cov-config=backbone-python/pyproject.toml --cov-report=xml:backbone-python/coverage.xml --cov-report=html:backbone-python/htmlcov

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
