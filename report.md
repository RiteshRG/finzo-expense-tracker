# Finzo Project Report

## 1. USE CASE DEFINITION

### 1.1 Problem Statement

Finzo is a server-rendered personal expense tracker for people who want to record spending and review totals and categories over a selected period. Users can create accounts, sign in, and manage their own expense records. The profile page presents account details, a spending summary, category totals, and transactions.

The repository identifies the intended use as personal expense tracking; it does not establish a narrower demographic. FastAPI, Jinja2, and MySQL fit the implemented web application: FastAPI handles HTTP requests, Jinja2 renders pages on the server, and PyMySQL stores user and expense data. The project instructions explicitly prefer direct, parameterized SQL and a routes/services/repositories separation rather than an ORM. The application is not an AI application: no AI model or AI-powered runtime feature is implemented.

### 1.2 Scope

#### In Scope

- Public landing, Terms, and Privacy pages.
- Registration, login, logout, and signed-session authentication.
- An authenticated profile with user-specific expense totals, category breakdown, recent activity, date presets, and custom date filtering.
- Authenticated expense creation, editing, and single-record deletion, scoped to the current user.
- An authenticated Analytics page that explicitly presents a “Coming Soon” placeholder.
- A database-backed `/health` endpoint and a Docker image definition.

#### Out of Scope

- Actual analytics charts, reports, or predictive insights; the Analytics specification explicitly limits the delivered page to a presentation-only placeholder.
- Budget management, recurring-payment automation, bank synchronization, and AI-generated advice; these features are not implemented in the routes, services, templates, or schemas.
- Profile editing, bulk deletion, undo/restore, and a JSON API; feature specifications describe the relevant profile and deletion work as read-only or single-record.
- Cloud-provider deployment, image publication, and automatic deployment; the pre-deployment specification excludes these.

### 1.3 Features

| Feature | Input | Output | Status |
|---|---|---|---|
| Public pages | HTTP request | Landing, Terms, or Privacy HTML | Implemented |
| Registration | Name, email, password | Validated account record; redirect to login | Implemented |
| Login and logout | Email/password; logout POST | Signed session established or cleared | Implemented |
| Profile and date filter | Authenticated session; optional date bounds | User profile, filtered spending summary, categories, and transactions | Implemented |
| Add expense | Title, amount, category, description | New expense for the authenticated user | Implemented |
| Edit expense | Expense ID and edited fields | Updated owned expense | Implemented |
| Delete expense | Expense ID and confirmation POST | Owned expense removed; profile redirect | Implemented |
| Analytics | Authenticated session | “Advanced Analytics — Coming Soon” page | Partial |
| Health check | HTTP request | JSON success or generic unavailable response based on MySQL connectivity | Implemented |
| Container packaging | Docker build context and environment configuration | Non-root FastAPI container definition with health check | Partial |

“Partial” for Analytics means only its authenticated placeholder page is implemented. “Partial” for container packaging means a Dockerfile and ignore rules exist, but this inspection found no evidence of an actual image build or container smoke run.

### 1.4 Non-functional Requirements

- **Maintainability:** Project instructions and implementation separate routes, services, repositories, database helpers, schemas, and templates. SQL is parameterized in repository functions.
- **Security:** Passwords are hashed with Werkzeug; session state uses Starlette `SessionMiddleware`; expense update and delete queries include the authenticated user ID. The session cookie uses `SameSite=Lax`; its `Secure` flag is controlled by an environment variable.
- **Configuration:** Database URL and session signing key are environment-based. Startup validates required configuration; production does not initialize or seed the database. Development initialization and demo seeding are separately gated.
- **Usability:** Pages use shared Jinja templates and CSS, form labels and feedback, accessible table markup, and responsive CSS breakpoints at 900px and 600px.
- **Testing:** Pytest tests exercise routes, validation, ownership, database helpers, health behavior, and static container configuration. The observed full-suite run is not fully passing; see §2.4.
- **Deployment readiness:** A Dockerfile sets a configurable port, runs as a non-root user, and defines a health check. No numerical performance target or benchmark is present in the repository.

## 2. APPLICATION FUNCTIONALITY AND BUILD QUALITY

### 2.1 Working Functionality

The routes and templates support the following demonstration flows:

> **[SCREENSHOT PLACEHOLDER — Figure 1: Finzo public landing page]**
>
> Insert screenshot here.

Show the public landing page, registration call to action, and Finzo's stated expense-tracking purpose. The example spending figures and chart illustration on this page are static presentation content, not live account data.

> **[SCREENSHOT PLACEHOLDER — Figure 2: Registration and validation]**
>
> Insert screenshot here.

Show the registration form and, if useful, its inline validation response. Registration accepts name, email, and password; the schema requires a password of at least eight characters.

> **[SCREENSHOT PLACEHOLDER — Figure 3: Login and authenticated navigation]**
>
> Insert screenshot here.

Show successful sign-in followed by the authenticated navigation and sign-out control. Logout is a POST action.

> **[SCREENSHOT PLACEHOLDER — Figure 4: Profile overview and date filtering]**
>
> Insert screenshot here.

Show the signed-in user's summary, custom date fields or date presets, category breakdown, transaction list, and empty states when applicable. The profile data is fetched through the profile service and user-scoped repositories.

> **[SCREENSHOT PLACEHOLDER — Figure 5: Add and edit expense forms]**
>
> Insert screenshot here.

Show the create form and a pre-populated edit form, including amount, category, and description fields plus validation feedback.

> **[SCREENSHOT PLACEHOLDER — Figure 6: Confirming expense deletion]**
>
> Insert screenshot here.

Show the profile transaction actions and the confirmation dialog. Confirmed deletion submits a POST and the route scopes deletion to the authenticated user.

> **[SCREENSHOT PLACEHOLDER — Figure 7: Analytics placeholder]**
>
> Insert screenshot here.

Show the authenticated Analytics page's visible “Coming Soon” status; do not represent it as functional analytics.

#### Known Limitations

- Analytics is intentionally only a “Coming Soon” presentation page; it does not query expense data or display charts.
- The landing page contains static illustrative totals and categories; they are not live dashboard values.
- Two observed profile tests fail while rendering the Edit URL in `templates/profile.html`: their stubbed transactions omit `id`, which the current template requires for route generation, and Starlette raises `AssertionError: Must not be empty`. The failing tests are `test_profile_renders_repository_backed_context` and `test_profile_route_passes_date_query_parameters_to_service`. This identifies a test-fixture/context-contract mismatch; it does not by itself establish a defect for repository-backed records, whose service context includes transaction IDs. The suite still needs investigation before it can be reported as fully passing.
- The test suite mocks database connectivity; no live MySQL integration result was established in this run.
- The repository contains a Dockerfile and tests that inspect it, but no verified Docker build or container health smoke-test result was found.
- No GitHub Actions workflow or other checked-in CI configuration is present in the tracked files.
- The seed-user and seed-expense prompts refer to `database/db.py`; the current database implementation is `database/__init__.py`. The prompt paths should be corrected before those prompts are relied on.
- No verified evidence was found for a real AI-generated incorrect output and its correction. See §3.3: **[TODO — NEED USER INPUT]**.

### 2.2 Code Structure

The repository uses a layered FastAPI/Jinja2 application. `app.py` creates the application, configures sessions and templates, includes routers, and provides public and health endpoints. Route modules handle HTTP/session behavior; services normalize data and build display contexts; repositories hold explicit MySQL queries; `database/` owns connections and query execution; `schemas.py` validates form payloads.

`templates/` contains the shared base and page templates. `static/` contains shared and landing-page CSS plus the deletion-dialog JavaScript. `tests/` contains pytest route, service, repository, database, and pre-deployment checks. `.github/` contains Copilot instructions, feature specs, plans, prompts, reviewer/test agents, and a frontend design skill. `requirements.txt` declares FastAPI, Uvicorn, Jinja2, PyMySQL, Pydantic, pytest, and related packages.

```text
.
├── app.py
├── database/                 # MySQL connection, query helpers, table contracts
├── dependencies/             # Session authentication helpers
├── repositories/             # Parameterized user and expense SQL
├── routes/                   # Auth, profile, expense, analytics, HTTP handling
├── services/                 # Auth, expense, and profile/business logic
├── schemas.py                # Pydantic input validation
├── templates/                # Shared layout and server-rendered pages/forms
├── static/                   # CSS and vanilla JavaScript
├── tests/                    # Pytest coverage
├── .github/
│   ├── agents/
│   ├── plan/
│   ├── prompts/
│   ├── skills/
│   └── specs/
├── requirements.txt
├── Dockerfile
└── .env.example
```

The main feature modules are relatively deep: for example, expense routes delegate normalization/validation to a service and SQL to a repository. Some endpoint logic remains in `app.py` for application-level health and public pages. This is not a universal “deep module” design, but responsibilities are separated where data workflows warrant it. There is no ORM or migration framework.

### 2.3 Refactoring

#### Refactoring Example 1 — Extracting the profile route and data access from `app.py`

**Before**

In the parent of commit `09c6641`, `app.py` contained the `/profile` handler directly. Profile repositories and the profile service were not yet part of that implementation.

**Problem**

The application entry point mixed page routing with profile behavior, leaving the profile data workflow without the later route/service/repository boundaries.

**After**

Commit `09c6641` added `routes/profile.py`, included its router from `app.py`, and added profile-service and repository-backed profile data handling. The route passes the authenticated user ID into the service and renders the template using its returned context.

**Why it is better**

HTTP/session handling, profile formatting/aggregation, and SQL access have distinct homes, making their responsibilities easier to test and change independently.

**Evidence**

`git show 09c6641 -- app.py routes/profile.py services/profile_service.py repositories/expense_repository.py`; current files: `app.py`, `routes/profile.py`, `services/profile_service.py`, and `repositories/expense_repository.py`.

#### Refactoring Example 2 — Generalizing profile queries for selectable date ranges

**Before**

Before commit `48bc132`, the profile repository exposed a month-specific `get_monthly_category_totals` operation and a recent-transactions query without date-range parameters.

**Problem**

The repository contract did not express the user-selected range needed by the profile's date filter.

**After**

Commit `48bc132` renamed the aggregation operation to `get_category_totals_for_range`, added start/end bounds to the transaction query, and introduced service helpers to resolve date ranges and presets. The profile route now accepts `start_date` and `end_date`.

**Why it is better**

The data-access contract reflects the filter used by the interface and uses explicit half-open timestamp bounds for the selected period.

**Evidence**

`git show 48bc132 -- routes/profile.py services/profile_service.py repositories/expense_repository.py`; current files: `routes/profile.py`, `services/profile_service.py`, `repositories/expense_repository.py`, and `templates/profile.html`.

### 2.4 TDD

The test suite consists of feature-oriented pytest modules, including `test_auth_login.py`, `test_database_layer.py`, `test_profile.py`, and numbered tests for date filtering, Analytics, expense creation, editing, deletion, and pre-deployment behavior. The tests use FastAPI's `TestClient`, mocks/monkeypatching for repository and database boundaries, and assertions for redirects, rendered forms, validation, user ownership, parameterized SQL, and health responses. The pre-deployment checks also inspect Dockerfile and `.dockerignore` properties; they do not themselves prove an image was built.

The test-feature prompt specifies a spec-first test-writing handoff: the test writer should derive expected behavior from the specification, followed by a test runner that runs only the feature test and diagnoses failures without modifying code. However, commit evidence does not establish that any test was written before its corresponding implementation. For example, add/edit implementation commits include their test files in the same commit, and the delete-test commit follows the deletion implementation commit.

**Observed execution:** `.\.venv\Scripts\python.exe -m pytest -q --tb=short` — **95 passed, 2 failed, 2 warnings**. Both failures are profile rendering tests and raise `AssertionError: Must not be empty` while generating an edit link from a transaction. This is a current-worktree result, not a claim that the committed baseline has been tested.

> **[SCREENSHOT PLACEHOLDER — Figure 8: Pytest execution and failure summary]**
>
> Insert screenshot here.

Use a terminal capture showing the command and the final pytest summary. Include the two failures rather than presenting the run as a passing build.

For the criterion “at least one test written before implementation”: **[TODO — NEED USER INPUT]**. Repository commits do not prove the required ordering.

### 2.5 Maintainability

- Routes, services, repositories, schemas, and database helpers are separated and named by responsibility.
- SQL is parameterized and expense mutation/lookups are scoped to the authenticated user.
- `DATABASE_URL`, `SESSION_SECRET_KEY`, and the session-cookie security setting are environment-controlled; `.env.example` documents variable names without containing usable secrets, and `.gitignore` excludes `.env` and `.env.docker`.
- Database and authentication failures are logged at the application boundary and receive generic user-facing responses in the inspected flows.
- Shared `base.html` provides navigation/footer and page blocks; CSS variables, responsive breakpoints, and reusable form styles are defined in the shared stylesheet.
- Feature specs state routes, schema/database expectations, files, constraints, and definitions of done. Copilot instructions constrain stack, security, and architecture; agents and prompts define testing and review handoffs.
- The test suite exercises many boundaries, but the observed two failures reduce confidence until resolved. No CI workflow is checked in.

## 3. PROMPTING STRATEGIES FOR BUILD QUALITY

### 3.1 Prompting Strategies

- **Project-context constraints:** `.github/copilot-instructions.md` establishes the FastAPI/MySQL/PyMySQL/Jinja2 stack, layered architecture, user ownership, secret handling, and parameterized SQL rules.
- **Specification-first feature work:** `.github/prompts/create-spec.md` directs inspection of the existing project and creates numbered feature specs with routes, data changes, files, constraints, and a definition of done. The numbered specs use acceptance criteria and explicit exclusions.
- **Constrained feature implementation:** Specs require reuse of existing auth, templates, and database helpers; prohibit unnecessary dependencies/ORMs; and call out user-scope and validation behavior.
- **Test-from-spec prompting:** `.github/prompts/test-feature.md` instructs a test-writer agent to derive tests from the spec, then hands the named file to a test-runner agent. It forbids silent code/test modification during diagnosis and disallows a live production database.
- **Parallel code review:** `.github/prompts/code-review-feature.md` requires both security and quality reviewers to inspect a scoped diff against the spec, then combines findings before asking permission to implement them.
- **Reusable UI context:** `.github/skills/frontend-design/SKILL.md` directs inspection of the actual project and use of the shared layout, CSS tokens, auth flow, and real validation evidence.
- **Development data prompts:** `seed-user.md` requests checking email uniqueness before insertion. `seed-expense.md` requires an existing user, parameterized SQL, and one transaction with rollback on failure. Both reference the absent `database/db.py`, which is stale relative to the current tree.
- **Deployment constraints:** `.github/specs/11-pre-deployment-testing.md` defines a platform-neutral pytest/Docker verification path, mocked database access, safe environment configuration, and explicit exclusions. No separate Docker/deployment prompt or CI workflow is present.

### 3.2 Prompt-to-Practice Mapping

| Prompt / Prompt Type | Development Practice | Purpose | Evidence |
|---|---|---|---|
| Copilot project instructions | Architecture and security constraints | Keep features consistent with direct MySQL/PyMySQL access, ownership checks, environment secrets, and layering | `.github/copilot-instructions.md` |
| Feature-spec prompt | Inspect, specify, plan, define done | Reduce assumptions and set verifiable feature acceptance criteria | `.github/prompts/create-spec.md`; `.github/specs/01-*.md` through `11-*.md` |
| Test-feature prompt | Spec-derived tests, then isolated test execution | Validate expected behavior without deriving tests from implementation | `.github/prompts/test-feature.md`; `.github/agents/finzo-test-writer.md`; `.github/agents/finzo-test-runner.md` |
| Code-review prompt | Parallel security and quality review | Separate review concerns and collect scoped findings before changes | `.github/prompts/code-review-feature.md`; `.github/agents/finzo-security-reviewer.md`; `.github/agents/finzo-quality-reviewer.md` |
| Frontend skill | Inspect existing system and reuse design conventions | Avoid parallel CSS/layout/auth implementations and encourage honest validation | `.github/skills/frontend-design/SKILL.md` and its references |
| Seed-data prompts | Constrained test-data creation | Require user verification, parameterized queries, and rollback on insertion failure | `.github/prompts/seed-user.md`; `.github/prompts/seed-expense.md` |
| Pre-deployment specification | Local tests and container checks, without provider-specific deployment | Check configuration/health and define Docker expectations without publishing or deploying | `.github/specs/11-pre-deployment-testing.md`; `Dockerfile`; `tests/test_11-pre-deployment-testing.py` |

### 3.3 What Worked / What Did Not

The repository contains detailed specifications and prompt instructions, but no versioned prompt/output transcript or unambiguous commit evidence recording a specific AI-generated error and its correction. The observed pytest failures establish current test failures, not that an AI generated the faulty output.

**[TODO — NEED USER INPUT: provide a documented AI-generated error/correction example, including the initial output, correction prompt, final result, and evidence.]**

A verifiable prompt-maintenance issue is that both seed prompts instruct the assistant to inspect `database/db.py`, which is absent; the actual database module is `database/__init__.py`. This is a stale prompt reference, not evidence of an AI-generated runtime defect.

## 4. AUDIT AND EVALUATION PIPELINE

### 4.1 Evaluation Pipeline

The workflow configured in the repository is:

```text
Copilot instructions and feature specification
                    ↓
Feature planning (where a matching plan exists)
                    ↓
Implementation in the existing FastAPI/service/repository structure
                    ↓
Test writer derives tests from the specification
                    ↓
Test runner executes only the requested feature test
                    ↓
Security reviewer + quality reviewer run in parallel
                    ↓
Pre-deployment pytest checks and Docker build/smoke-test procedure
                    ↓
Manual final review
```

The test and review handoffs are defined by prompts/agents; their presence does not prove that every stage ran for every feature. The current report-time pytest suite was executed and produced 95 passes and 2 failures. Database checks in tests are mocked. `tests/test_11-pre-deployment-testing.py` checks health behavior, startup configuration, and Dockerfile/ignore-file content, while `.github/specs/11-pre-deployment-testing.md` describes actual Docker build and smoke checks. No Docker build/smoke result or CI execution evidence was found. There is no tracked `.github/workflows/` directory, so the evidenced pipeline is local/manual rather than a checked-in automated CI/CD pipeline.

## 5. OVERALL EVALUATION

Finzo has a concrete, functioning core for authenticated personal expense tracking: accounts, session-based access, per-user expense CRUD, profile summaries, and date filters. Its architecture and project-specific specifications provide useful constraints for continued AI-assisted development. Analytics remains a declared placeholder, and deployment automation is not present.

The current quality gate is **not fully green**: the observed pytest run has two profile-rendering failures that need investigation. A clean result requires rerunning the suite after resolving them. Repository history supports two profile structure changes, but does not prove test-first ordering or document a concrete AI-output correction.

**Items requiring user evidence or follow-up**

- Resolve and rerun the two failing profile tests.
- **[TODO — NEED USER INPUT]** Provide evidence that at least one test was written before implementation, if this is a required project claim.
- **[TODO — NEED USER INPUT]** Provide a documented AI-generated incorrect/incomplete output and its correction for §3.3.
- Run and record a real Docker build and container health smoke test if deployment verification is required.
