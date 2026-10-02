# Finzo — GitHub Copilot Instructions

## Project Overview

Finzo is a full-stack personal expense tracker built with **FastAPI, Python, MySQL, PyMySQL, Jinja2, HTML, CSS, and JavaScript**.

## Architecture

Follow a layered architecture with the following responsibilities:

| File                              | Responsibility                                                   |
| --------------------------------- | ---------------------------------------------------------------- |
| `routes/auth.py`                  | Handles registration, login and logout HTTP requests.            |
| `services/auth_service.py`        | Handles password hashing, verification and authentication logic. |
| `repositories/user_repository.py` | Creates and retrieves users in MySQL using explicit Python SQL. |
| `dependencies/auth.py`            | Checks user sessions and retrieves the authenticated user.       |
| `routes/expenses.py`              | Handles expense requests and protects authenticated operations.  |
| `database.py`                     | Configures MySQL connections, database helpers, and query logic. |
| `models.py`                       | Defines User and Expense data structures and table contracts.     |
| `schemas.py`                      | Validates registration, login and expense data.                  |

## Development Rules

1. Maintain clear separation between routes, services and repositories.
2. Use **FastAPI** for backend endpoints and **Jinja2** for server-rendered templates.
3. Use **Pydantic schemas** for input validation.
4. Use **Python** to communicate directly with **MySQL** through **PyMySQL**.
5. Write SQL queries explicitly in Python; do not use SQLAlchemy.
6. Use **MySQL** as the project's database. Do not introduce PostgreSQL, SQLite, MongoDB, or another database.
7. Do not introduce **SQLAlchemy**, **Alembic**, another ORM, or another migration framework.
8. Keep authentication and authorization logic on the backend.
9. Ensure users can access only their own expenses.
10. Never store passwords in plain text. Always use secure password hashing.
11. Keep database credentials, secret keys and other sensitive configuration in environment variables.
12. Use `DATABASE_URL` or an equivalent environment-based configuration for MySQL connection details.
13. Keep database connection and query logic in the database layer and keep SQL/database operations separated from routes.
14. Follow the existing project structure and avoid unnecessary changes.
15. Write maintainable, modular and readable code.
16. Use proper database relationships and constraints for users and expenses.
17. Use parameterized/database-safe SQL queries; do not construct SQL using unsafe string interpolation.

## Instructions for Copilot

* Inspect relevant existing files before modifying them.
* Follow the architecture and coding rules defined here.
* Place new functionality in the appropriate layer.
* Avoid duplicating existing functionality.
* Preserve existing working features when implementing changes.
* Do not introduce unnecessary frameworks, libraries or architectural patterns.
* Do not switch the database from MySQL to another database.
* Do not introduce SQLAlchemy, Alembic, another ORM, or another migration framework.
* Keep database credentials out of source code.
* Keep database connection/session handling in the database layer.
* Explain significant architectural changes and list modified files.
* Run relevant tests after implementation and report the results.
