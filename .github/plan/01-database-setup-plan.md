# Database Setup Implementation Plan

## TL;DR

Use the existing root-level placeholders in `database.py` and `models.py`, add a direct MySQL connection layer powered by PyMySQL, implement explicit SQL queries in Python, and keep initialization safe and idempotent through startup seeding.

This project should not use SQLAlchemy, Alembic, or another ORM. The database approach is direct Python + MySQL through PyMySQL.

---

## Findings from the Repo

- `app.py` is the active FastAPI entrypoint and currently contains only static page routes; it does not yet bootstrap the database.

- `database.py` and `models.py` are empty placeholders, so the database layer is not implemented yet.

- `db.py` is only a stub note and should not become a second source of truth.

- `.gitignore` already ignores `.env`, which is consistent with keeping database credentials out of source control.

- A project-wide search did not reveal any SQLAlchemy or Alembic setup, so the implementation should remain fully direct and explicit.

- The specification at `01-database-setup.md` now reflects the direct Python + MySQL approach instead of the ORM-based approach.

---

# Implementation Plan

## 1. Consolidate the Database Configuration in the Existing Project Structure

Use the existing project files as the main database setup and avoid creating a parallel duplicate under `database` unless absolutely required.

Add:

- a MySQL connection helper
- a reusable query execution pattern
- initialization helpers
- seed helpers
- a `DATABASE_URL`-based configuration

Use the MySQL connection format:

```text
mysql+pymysql://username:password@localhost:3306/finzo_dev
```

The configuration must read connection details from environment variables and never hardcode credentials.

---

## 2. Define the Database Schema in Python

Create the required table contracts in Python using direct connection logic.

The initial schema should include:

- `users` table
- `expenses` table
- primary keys on both tables
- unique email constraint on `users.email`
- foreign key from `expenses.user_id` to `users.id`
- required `NOT NULL` checks for required fields

Keep the schema simple and aligned with the app’s personal expense tracker requirements.

---

## 3. Add Safe Initialization and Seed Logic

Create an `init_db()` helper that runs explicit SQL to create missing tables without deleting existing data.

Create a `seed_db()` helper that inserts one demo user and eight sample expenses only if they do not already exist.

The seed routine must be idempotent so repeated runs do not create duplicate rows.

Keep seed data development-only and do not mix it with production logic.

---

## 4. Wire the Database into the FastAPI App

Update `app.py` to trigger the initialization during startup, but keep all database logic in the database layer rather than inside routes.

Do not add auth or expense CRUD logic in this task.

The goal is to establish a stable MySQL foundation without altering unrelated functionality.

---

## 5. Validate Dependencies and Environment Configuration

Check `requirements.txt` for the required MySQL driver and ensure `pymysql` is installed.

Keep `.env` ignored and provide an example environment file if needed.

Explicitly avoid SQLAlchemy, Alembic, and other ORM or migration frameworks for this task.

---

## Verification Checklist

1. Confirm the app imports with a valid `DATABASE_URL` set.
2. Confirm the database tables are created successfully.
3. Run the initializer twice and ensure no duplicate rows are created.
4. Run the seed function twice and ensure the demo user and demo expenses remain stable.
5. Confirm the app still boots without route-level database logic leaking into the UI layer.

---

## Scope Boundaries

In scope:

- MySQL connection
- direct Python SQL queries
- schema creation
- initialization and safe seeding
- environment-based configuration

Out of scope:

- login flow
- registration logic
- dashboard features
- expense CRUD endpoints
- SQLAlchemy
- Alembic
- any other ORM or database abstraction