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

echo "==> Go: backbone-go coverage"
(cd backbone-go && go test ./... -coverprofile=coverage.out -covermode=atomic)

echo "==> Go: examples/go/clean-api-go coverage"
(cd examples/go/clean-api-go && go test ./tests/... -coverprofile=coverage.out -covermode=atomic)

echo "==> Go: golangci-lint (backbone-go)"
(cd backbone-go && golangci-lint run --out-format json > golangci-lint-report.json || true)

echo "==> Go: golangci-lint (examples/go/clean-api-go)"
(cd examples/go/clean-api-go && golangci-lint run --out-format json > golangci-lint-report.json || true)

echo "==> Python: backbone-python coverage"
(cd backbone-python && python -m pytest tests/ --cov=backbone --cov-report=xml)

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
