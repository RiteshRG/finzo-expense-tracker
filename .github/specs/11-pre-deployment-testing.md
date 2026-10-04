# Spec: Pre-deployment Testing

## Overview

Add a repeatable pre-deployment verification path for Finzo so code and the container image can be checked before release. The checks must run without access to a developer's or production MySQL database, must fail clearly when required deployment configuration is missing, and must exercise the same application entry point and HTTP behavior used by the container.

Keep this platform-neutral: do not add a cloud-provider deployment, publish images, or deploy automatically. Use the existing pytest suite for application checks and Docker for building and smoke-testing the deployment image. Do not run destructive tests against a live database.

## Depends on

- Existing FastAPI app and routes in `app.py` and `routes/`.
- Existing pytest suite in `tests/` and dependencies in `requirements.txt`.
- Existing environment-variable configuration documented by `.env.example`.
- Existing `.dockerignore` and the currently empty `Dockerfile`.

## Routes

- Add an unauthenticated `GET /health` endpoint with a stable JSON response for container and deployment smoke checks.
  - Keep the endpoint free of user data and secrets.
  - Return a success status only when the service is ready to accept requests, including a successful database connectivity check.
  - Return an appropriate non-success status if the database is unavailable; do not expose connection strings, credentials, or raw database errors.
  - Keep this endpoint narrowly scoped to operational health; do not add metrics or an administrative interface.

## Database changes

No schema or migration changes are required. Provision the existing MySQL tables before production startup; production startup validates configuration but does not run schema creation or demo seeding.

Add or reuse a small database-layer health check that verifies a connection to the configured MySQL database and always closes the connection. Do not add SQL to the route. Tests must mock this check rather than require a live MySQL instance.

## Templates

### Create

None.

### Modify

None. The health response is machine-readable and does not use a template.

## Files to change

- `app.py` — register the health endpoint and ensure application startup failures are surfaced instead of being silently swallowed.
- `database/__init__.py` — provide a minimal database connectivity check using the existing PyMySQL connection helper.
- `Dockerfile` — replace the empty file with a minimal production-oriented image definition that installs declared requirements, runs the existing ASGI app on a configurable container port, and does not copy local secrets or development artifacts.
- `.dockerignore` — keep `.env`, virtual environments, caches, and Git metadata out of the build context; adjust only if needed for the Docker build.
- `requirements.txt` — only if a missing runtime dependency is required; do not add a test or container framework without need.

## Files to create

- `tests/test_11-pre-deployment-testing.py` — cover health success and database-unavailable behavior, startup configuration/failure handling, and container-relevant app startup without connecting to a real database.

## New dependencies

None expected. Use the existing pytest, FastAPI, HTTPX, and PyMySQL dependencies. Docker is an external build/runtime prerequisite, not a Python package dependency.

## Rules for implementation

- Keep MySQL as the only database and use the existing PyMySQL helper; do not introduce an ORM, migrations, SQLite, or a second database implementation.
- Keep database connectivity logic in `database/`, not in `app.py` route code.
- Keep all credentials and signing keys in environment variables. Never copy `.env` into the image or hard-code secrets.
- Do not swallow startup or health-check failures. Log useful operational context without exposing credentials or internal exception details to HTTP clients.
- Do not seed demo users or expenses as a side effect of production startup. Preserve any existing development seeding behavior only when explicitly configured for development or tests.
- Make tests deterministic: mock external database access, avoid requiring a running MySQL server, and do not rely on local `.env` values.
- Build the image from the repository root using `.dockerignore`; run it with explicitly supplied deployment environment variables and a configurable port.
- Do not publish an image, deploy to an external service, add provider-specific workflows, or change unrelated application behavior.
- Preserve existing route behavior and run the existing regression suite along with the new tests.

## Definition of done

- [ ] `pytest` can run the new pre-deployment checks without a live MySQL database or developer `.env` file.
- [ ] Tests verify that the health endpoint returns success when the database is reachable and a non-success status when it is unavailable, without exposing secrets.
- [ ] Tests verify that missing required configuration and application startup failures fail explicitly rather than being reported as successful startup.
- [ ] Production startup does not silently seed demo account or expense data; development/test seeding is explicitly controlled and covered.
- [ ] `docker build` from the repository root succeeds using the declared dependencies and excludes `.env`, virtual environments, and `.git`.
- [ ] The built image starts the FastAPI app on its configured port with environment-based configuration.
- [ ] A container smoke check can reach the health endpoint and observes failure when the database is unavailable.
- [ ] Existing authentication, expense, profile, and analytics tests continue to pass.
- [ ] No cloud-provider deployment, image publication, schema change, new database, ORM, secret, or unrelated feature is introduced.
