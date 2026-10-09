# Finzo

**An AI-assisted, spec-driven build of a personal expense tracker.**

Finzo is a server-rendered expense tracker (FastAPI, Jinja2, MySQL). The app is the *topic*. The real focus of this repository is **how it was built**: with an AI coding copilot, guided by written specifications, project rules, reusable prompts, review agents and automated tests.

> Finzo is **not** an AI-powered product. No AI model runs inside the app. AI is used only as a development tool.

---

## What this project demonstrates

| Practice | How it is done here | Where to look |
|---|---|---|
| **Spec-driven development (SDD)** | Every feature starts as a numbered spec with routes, data changes, files, constraints, exclusions and a definition of done | `.github/specs/01-*.md` to `11-*.md` |
| **Project rules for the copilot** | One instructions file fixes the stack, layering, user ownership, secret handling and parameterized SQL | `.github/copilot-instructions.md` |
| **Reusable prompts** | Prompts for writing specs, testing, code review and seed data | `.github/prompts/` |
| **Specialised agents** | Separate test-writer, test-runner, security-reviewer and quality-reviewer agents | `.github/agents/` |
| **Skills** | A frontend-design skill so the copilot reuses the existing layout, CSS and auth flow | `.github/skills/frontend-design/SKILL.md` |
| **Tests derived from specs** | Test writer reads the spec, test runner runs only that feature's test and diagnoses without editing code | `tests/`, `.github/prompts/test-feature.md` |
| **Parallel review** | Security and quality reviewers check the same scoped diff against the spec | `.github/prompts/code-review-feature.md` |
| **Refactoring with evidence** | Two documented before/after refactors tied to commits | see [Refactoring](#refactoring-examples) |

---

## The SDD workflow

Each feature follows the same loop, wrapped in git steps so every feature has its own branch and pull request.

```mermaid
flowchart TD
    A([START: trigger]) --> B[Pull latest main<br/>git pull origin main]
    B --> C[Create branch<br/>git checkout -b feature/x]
    C --> D[Switch to branch<br/>git switch feature/x]
    D --> E[Spec]
    E --> F{{Review and approval}}
    F --> G[Design]
    G --> H{{Review and approval}}
    H --> I[Tasks]
    I --> J[Build]
    J --> K[Validate]
    K --> L{{Validation gate}}
    L --> M[Commit<br/>git commit -m]
    M --> N[Push to GitHub<br/>git push origin]
    N --> O[Create and merge PR]
    O --> P[Delete branch<br/>git branch -d]
    P --> Q[Switch to main<br/>git switch main]
```

- **Spec and design** are each reviewed and approved before the next step.
- **Validate** runs the feature test, the security and quality reviews, and the pre-deployment checks.
- Nothing is committed, pushed or merged until the **validation gate** passes.

The prompts and agents define these steps. Their presence does not prove that every step ran for every feature.

---

## How the AI copilot was used

- **Tool:** GitHub Copilot in VS Code, agent mode.
- **Models:** Copilot automatic model selection for coding and diagnosis, GPT-5 mini for test writing, Claude Sonnet for security and quality review. Using a different model for review gives a second view of the code.
- **Prompt files:** the important prompts and agents are stored in `.github/` so the process is repeatable.

| File | Purpose |
|---|---|
| `copilot-instructions.md` | Project rules: stack, architecture, security, secrets |
| `prompts/create-spec.md` | Inspect the project and write a numbered feature spec |
| `prompts/test-feature.md` | Spec-based test writing, then an isolated test run |
| `prompts/code-review-feature.md` | Run both reviewers on a scoped diff |
| `prompts/seed-user.md`, `prompts/seed-expense.md` | Create demo data safely (uniqueness check, one transaction with rollback) |
| `agents/finzo-test-writer.md` | Derive tests from the spec |
| `agents/finzo-test-runner.md` | Run one feature test and diagnose without editing code |
| `agents/finzo-security-reviewer.md` | Security review against the spec |
| `agents/finzo-quality-reviewer.md` | Quality review against the spec |
| `skills/frontend-design/SKILL.md` | Reuse the existing layout, CSS tokens and auth flow |

### Prompting that improved results

Example: the landing-page hero (commit `d7100f4`).

- **First prompt:** "Create a hero section for the Finzo expense-tracking website." The result was mostly text and gave no visual idea of the product.
- **Improved prompt:** attach a reference image, ask the copilot to match its composition without copying it blindly, and tell it to follow `.github/skills/frontend-design/SKILL.md` (keep the theme, typography and shared CSS, make it responsive).
- **Result:** a hero with a headline, sign-up button, a spending-chart visual and summary cards.

The original prompt and first output were not saved, so this description is reconstructed.

### Refactoring examples

| Commit | Before | After |
|---|---|---|
| `09c6641` | The `/profile` handler lived in `app.py` | Split into `routes/profile.py`, a profile service and a repository |
| `48bc132` | Month-only `get_monthly_category_totals` | `get_category_totals_for_range` with start and end bounds, matching the date filter in the UI |

---

## Code quality and audit

**Architecture.** Responsibilities are separated: routes (HTTP), services (logic), repositories (SQL), schemas (validation), database helpers. No ORM. SQL is parameterized and every expense query is scoped to the signed-in user.

**Tests.** pytest modules per feature, using mocks at database boundaries. Latest recorded result: **95 passed, 2 failed, 2 warnings**. Both failures are profile tests whose mocked transactions omit the `id` that the template needs for the Edit link. This is a fixture mismatch, not a proven defect for real records.

**Known gaps ("broken windows").**

| Gap | Status |
|---|---|
| 2 failing profile tests (missing `id` in stubs) | Open |
| Seed prompts point to `database/db.py`, which does not exist (the module is `database/__init__.py`) | Open |
| Landing page mentions budgets and a date input that the product does not have | Open |
| Tests mock the database, so no live MySQL integration test | Accepted |
| No CI workflow checked in | Deferred |
| Docker build and container health check not verified | Deferred |

A full write-up with screenshots, evidence and prompt log is in `report.md`.

---

## The app (the topic)

Finzo lets a user create an account, sign in and manage their own expenses. The profile page summarises spending and supports date filtering.

**Features**

- Registration, login and logout with signed sessions
- Create, edit and delete expenses
- Profile summaries, category breakdowns, recent transactions and date filters
- Responsive landing, profile and expense pages
- An Analytics placeholder marked "Coming Soon"
- A database-backed `/health` endpoint

**Not implemented:** analytics charts, budgets, bank sync, recurring payments, AI-generated advice.

**Stack:** Python, FastAPI, Jinja2, HTML, CSS, vanilla JavaScript, MySQL with PyMySQL (explicit parameterized SQL), pytest, Docker.

### Project layout

```text
app.py                  FastAPI application and public routes
database/               MySQL connection helpers and table definitions
dependencies/           Authentication and session dependencies
repositories/           Parameterized SQL and persistence operations
routes/                 HTTP endpoints
services/               Application and business logic
schemas.py              Pydantic input validation
templates/              Jinja2 page templates
static/                 CSS and JavaScript
tests/                  Pytest route, service, repository and database tests
.github/                Copilot instructions, specs, prompts, agents, skills
```

---

## Run it locally

**Requirements:** Python 3.12 or newer, a running MySQL server with credentials, PowerShell (Windows) or a terminal (macOS/Linux).

**1. Create and activate a virtual environment**

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

```bash
python3 -m venv .venv
source .venv/bin/activate
```

**2. Install dependencies**

```bash
python -m pip install -r requirements.txt
```

**3. Configure environment variables**

Copy `.env.example` to `.env` and set your values. Never commit `.env`.

```dotenv
DATABASE_URL=mysql://your_mysql_user:your_mysql_password@localhost:3306/finzo_dev
APP_ENV=development
SEED_DEMO_DATA=false
SESSION_SECRET_KEY=replace_with_a_random_secret_at_least_32_characters_long
SESSION_COOKIE_SECURE=false
```

Generate a key with:

```bash
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

- Startup validates the MySQL URL and session key.
- In `development` and `test`, startup creates the tables. The MySQL account must be allowed to create the database if it does not exist.
- Demo seeding runs only when `SEED_DEMO_DATA=true`.
- For production, set `APP_ENV=production`, use a secure key, set `SESSION_COOKIE_SECURE=true` over HTTPS, and create the database and tables beforehand.

**4. Start the server**

```bash
python -m uvicorn app:app --reload --host 127.0.0.1 --port 5001
```

Open <http://127.0.0.1:5001/>. The health check is at <http://127.0.0.1:5001/health>.

**5. Run the tests**

```bash
python -m pytest -q
```

The tests mock the database, so passing tests are not a live MySQL integration test. Rerun the suite to check the current state.

### Docker

```bash
docker build -t finzo .
```

Provide the required environment variables and a MySQL service reachable from the container. It listens on port `8000` by default (override with `PORT`) and has a health check on `/health`. A Dockerfile alone does not prove deployment; verify the build and run in your target environment.
