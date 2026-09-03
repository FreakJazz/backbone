# Changelog

All notable changes to Backbone Framework will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] - 2026-09-03

> Note: this is the first version actually cut as a git tag. The `[1.0.0]`
> entry below describes the feature set as of the initial commit but was
> never tagged — `pyproject.toml`/`__init__.py.__version__` had stayed at
> `0.1.0` the whole time. Versioning starts here for real, at `0.2.0`, to
> avoid re-using `1.0.0` for a different, already-tagged codebase.

### Added
- 🔀 **Cursor (keyset) pagination** — `domain.specifications.encode_cursor`/
  `decode_cursor` (opaque `base64({"v": ..., "id": ...})` tokens, cross-decodable
  with backbone-go's Go implementation) and `CursorPaginatedResponseBuilder`.
  Existing offset pagination (`page`/`page_size`) is unchanged; this is an
  additive alternative for deep paging without the `OFFSET` cost.
- 🧰 `PaginatedResponseBuilder.success`/`SimpleObjectResponseBuilder.found` now
  accept any object, not just `dict` — callers can pass a tagged
  dataclass/Pydantic model straight through instead of flattening it first.

### Fixed
- Pydantic v1-style config (`Field(env=...)`, `class Config`, `@validator`,
  `.dict()`) migrated to native Pydantic v2 API in
  `infrastructure/configuration/base_config.py` — removes `DeprecationWarning`
  noise under Pydantic 2.x, which is what `dependencies` has required all along.
- `datetime.utcnow()` (deprecated in Python 3.12) replaced with
  `datetime.now(timezone.utc)` in `domain/exceptions/base_kernel_exception.py`
  and `infrastructure/logging/structured_logger.py`; introduced
  `format_timestamp_utc_z()` so the wire format (`...Z` suffix, matching
  backbone-go's JSON encoding of `time.Time`) stays correct now that the
  underlying datetime is timezone-aware instead of naive.
- `DeprecationWarning: __package__ != __spec__.parent`, raised by pytest
  re-importing `backbone/__init__.py` under a synthetic module name during
  collection — fixed by reconciling `__spec__.name`/`__spec__.submodule_search_locations`
  with the `__package__` bootstrap override instead of trying to assign the
  read-only `__spec__.parent` property directly.
- `TestJsonFileEventStore` (tests/test_application.py) wrote real files into
  the repo's working tree (`test_events.json/`) — now uses an isolated
  `tempfile.mkdtemp()` directory, cleaned up in `tearDown()`.
- Stale test assertion in `test_domain.py`'s LIKE-specification coverage
  that expected an unwrapped value contrary to `NewLikeSpecification`'s
  documented auto-`%wrap%` behavior.

### Infrastructure
- Added `.github/workflows/ci.yml` — build/test gate on every push and PR
  (previously only `publish.yml` existed, which only ever fires behind a
  GitHub Release this project has never cut).
- Rewrote `.github/workflows/publish.yml`: fixed working-directory (every
  step ran from the repo root, where there's no `pyproject.toml`); replaced
  the GitHub-Packages publish step, which could never have worked (GitHub
  Packages has no generic Python/pip registry), with attaching the built
  wheel/sdist to the GitHub Release itself.
- Added `.github/workflows/sonarcloud.yml` + root `sonar-project.properties`
  (SonarCloud, CI-facing) and `docker-compose.sonarqube.yml` +
  `sonar-project.local.properties` (self-hosted SonarQube via Docker,
  broader scope including the `examples/` apps, with `ruff`/`bandit`/`mypy`
  findings layered on top of Sonar's own rules — see `scripts/run-sonar-local.*`).

## [1.0.0] - 2026-04-01

### Added
- 🏗️ **Clean Architecture Implementation**
  - Strict layer separation (Domain, Application, Infrastructure, Interfaces)
  - Dependency inversion principle enforced
  - Hexagonal architecture patterns

- 🔢 **8-Digit Exception System**
  - Domain exceptions: 11XXXXXX
  - Application exceptions: 10XXXXXX
  - Infrastructure exceptions: 12XXXXXX
  - Interface exceptions: 13XXXXXX

- 🎯 **Specification Pattern**
  - Dynamic filtering with Django-style syntax
  - Composable specifications (AND, OR, NOT)
  - Support for complex queries

- 📋 **Repository Pattern**
  - Abstract repository interfaces
  - Mock repository for testing
  - Ready for SQLAlchemy/MongoDB adapters

- 🔧 **Response Builders**
  - ProcessResponseBuilder for operations
  - PaginatedResponseBuilder for listings
  - SimpleObjectResponseBuilder for single objects
  - ErrorResponseBuilder for consistent errors

- 📊 **Structured Logging**
  - JSON formatter for ELK Stack
  - Context managers for request/operation tracking
  - Layer-specific loggers

- 🔄 **Event-Driven Architecture**
  - BaseEvent, DomainEvent, IntegrationEvent, SystemEvent
  - Event handlers with retry policies
  - Event stores (in-memory and file-based)
  - Adapters for Kafka, RabbitMQ, Redis

- 🧪 **Testing Framework**
  - BaseTestCase with async support
  - EventAwareTestCase for event testing
  - Mock implementations for all ports
  - Exception assertion helpers

- 📦 **Build and Distribution**
  - Modern pyproject.toml configuration
  - GitHub Actions workflow for automated publishing
  - GitHub Packages integration
  - Comprehensive documentation

### Documentation
- Complete README with examples
- Installation guide for GitHub Packages
- Workflow documentation for CI/CD
- Usage examples with FastAPI
- Type hints throughout the codebase

### Infrastructure
- GitHub Actions CI/CD pipeline
- Automated testing on push
- Release automation
- Package publishing to GitHub Packages

## [Unreleased]

### Planned Features
- SQLAlchemy adapter for repositories
- MongoDB adapter for repositories
- Redis cache integration
- Prometheus metrics support
- OpenTelemetry tracing
- GraphQL interface layer support
- gRPC interface layer support
