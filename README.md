# Finzo

Finzo is a server-rendered personal expense tracker. Users can create an account, sign in, and manage their own expenses. The profile page summarizes spending and supports date filtering.

## Features

- User registration, login, and logout with signed sessions
- Create, edit, and delete expenses
- Profile spending summaries, category breakdowns, recent transactions, and date filters
- Responsive landing, profile, and expense pages
- An Analytics page placeholder marked “Coming Soon”
- A database-backed `/health` endpoint

Expense data is scoped to the authenticated user. Analytics charts, budgets, bank synchronization, recurring payments, and AI-generated financial advice are not implemented.

## Technology

- Python and FastAPI
- Jinja2 templates, HTML, CSS, and vanilla JavaScript
- MySQL accessed with PyMySQL and explicit parameterized SQL
- Pytest for automated tests

The project does not use an ORM. Application code is organized into routes, services, repositories, schemas, and database helpers.

## Requirements

- Python 3.12 or newer
- A running MySQL server and credentials
- PowerShell on Windows, or a terminal on macOS/Linux

## Local setup

### 1. Create and activate a virtual environment

Windows PowerShell:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

macOS/Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 2. Install dependencies

```bash
python -m pip install -r requirements.txt
```

### 3. Configure environment variables

Copy `.env.example` to `.env`, then set the values for your environment. Never commit `.env`.

```powershell
Copy-Item .env.example .env
```

Example configuration:

```dotenv
DATABASE_URL=mysql://your_mysql_user:your_mysql_password@localhost:3306/finzo_dev
APP_ENV=development
SEED_DEMO_DATA=false
SESSION_SECRET_KEY=replace_with_a_random_secret_at_least_32_characters_long
SESSION_COOKIE_SECURE=false
```

Use a unique, random `SESSION_SECRET_KEY` of at least 32 characters. For example, generate one with:

```bash
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

The application validates the MySQL URL and session key during startup. In `development` and `test` environments, startup initializes the database tables; the MySQL account must have permission to create the configured database if it does not already exist. Demo-data seeding is disabled by default and only runs when `SEED_DEMO_DATA=true`.

For production, set `APP_ENV=production`, use a secure session key, and set `SESSION_COOKIE_SECURE=true` when serving over HTTPS. Provision the MySQL database and tables before starting the app; automatic schema initialization is restricted to development and test environments.

### 4. Start the development server

```bash
python -m uvicorn app:app --reload --host 127.0.0.1 --port 5001
```

Open <http://127.0.0.1:5001/>. The application also exposes a database connectivity check at <http://127.0.0.1:5001/health>.

## Tests

Run the complete pytest suite from the repository root:

```bash
python -m pytest -q
```

The route and repository tests use mocks for database boundaries; passing tests do not constitute a live MySQL integration test. The latest suite result recorded in `report.md` was **95 passed, 2 failed, 2 warnings**. Both failures were profile-rendering tests whose mocked transactions omitted an `id` required by the template to generate an edit link. Rerun the suite to check the current state.

## Docker

The repository includes a Dockerfile. Build the image with:

```bash
docker build -t finzo .
```

Run it by providing the required environment variables and a MySQL service reachable from the container. The container listens on port `8000` by default; the `PORT` environment variable can override it. The image includes a health check that calls `/health`. A successful image build or container run should be verified in the target environment; the presence of the Dockerfile alone does not demonstrate deployment.

## Project layout

```text
app.py                  FastAPI application and public routes
database/               MySQL connection helpers and table definitions
dependencies/           Authentication/session dependencies
repositories/           Parameterized SQL and persistence operations
routes/                 HTTP endpoints
services/               Application and business logic
schemas.py              Pydantic input validation
templates/              Jinja2 page templates
static/                 CSS and JavaScript
tests/                  Pytest route, service, repository, and database tests
.github/                Copilot instructions, specs, prompts, agents, and skills
```
