#!/usr/bin/env bash
# Generates every report sonar-project.local.properties expects, then runs
# the self-hosted scanner from docker-compose.sonarqube.yml.
#
# Prereqs: SonarQube already up (docker compose -f docker-compose.sonarqube.yml
# up -d), SONAR_TOKEN exported (see that file's header comment), and the Go
# and Python toolchains + linters on PATH:
#   go install github.com/golangci/golangci-lint/cmd/golangci-lint@latest
#   pip install ruff bandit mypy   (or: pip install -e "backbone-python[dev]")
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."

if [ -z "${SONAR_TOKEN:-}" ]; then
  echo "SONAR_TOKEN is not set — see docker-compose.sonarqube.yml's header comment." >&2
  exit 1
fi

# `go test ./... -coverprofile=...` produces no file at all here: both Go
# modules' tests live in external test packages under tests/ (exercising
# the library through its public API, not from inside each package), so
# `./...` also matches every production package directory, which has no
# _test.go files of its own — go test never merges a coverage profile in
# that mixed shape (verified: silently no coverage.out, no error). Scoping
# the *test target* to ./tests/... while using -coverpkg=./... to still
# instrument (and attribute coverage to) the production packages is what
# actually produces a valid, non-empty profile.
echo "==> Go: backbone-go coverage"
(cd backbone-go && go test ./tests/... -coverpkg=./... -coverprofile=coverage.out -covermode=atomic)

echo "==> Go: examples/go/clean-api-go coverage"
(cd examples/go/clean-api-go && go test ./tests/... -coverpkg=./... -coverprofile=coverage.out -covermode=atomic)

echo "==> Go: golangci-lint (backbone-go)"
(cd backbone-go && golangci-lint run --out-format json > golangci-lint-report.json || true)

echo "==> Go: golangci-lint (examples/go/clean-api-go)"
(cd examples/go/clean-api-go && golangci-lint run --out-format json > golangci-lint-report.json || true)

# Run from the repo root (not `cd backbone-python && pytest tests/`) so
# coverage.py's `relative_files = true` (pyproject.toml) records paths
# relative to the repo root ("backbone-python/domain/...") — matching what
# sonar.sources expects. Run from inside backbone-python instead and the
# same setting records paths relative to *that* directory ("domain/...",
# "conftest.py"), which the scanner then can't resolve at all (verified:
# every file's coverage measure silently dropped, "Cannot resolve the file
# path 'conftest.py'"). --cov-config is explicit because coverage.py's own
# config auto-discovery looks in the current directory (the repo root here,
# which has no [tool.coverage] section of its own).
echo "==> Python: backbone-python coverage"
python -m pytest backbone-python/tests --cov=backbone --cov-config=backbone-python/pyproject.toml --cov-report=xml:backbone-python/coverage.xml --cov-report=html:backbone-python/htmlcov

echo "==> Python: ruff"
ruff check backbone-python examples/python/clean_api_python --output-format=json > ruff-report.json || true

echo "==> Python: bandit"
bandit -c bandit.yaml -r backbone-python examples/python/clean_api_python -f json -o bandit-report.json || true

echo "==> Python: mypy"
mypy backbone-python examples/python/clean_api_python > mypy-report.txt || true

# golangci-lint/ruff/bandit/mypy all `|| true` above: a nonzero exit there
# means "found issues to report", not "failed to run" — the analysis is the
# point of this script, so a lint finding must not abort it before the scan
# that's supposed to surface that same finding in SonarQube.

echo "==> SonarQube scan"
docker compose -f docker-compose.sonarqube.yml run --rm scanner

echo "==> Done — see http://localhost:9000/dashboard?id=backbone-local"
