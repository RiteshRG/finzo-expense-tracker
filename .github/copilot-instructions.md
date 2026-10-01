# Finzo — GitHub Copilot Instructions

## Project Overview

Finzo is a full-stack personal expense tracker built with FastAPI, Jinja2, HTML, CSS, JavaScript and PostgreSQL.

## Architecture

Follow a layered architecture with the following responsibilities:

| File                              | Responsibility                                                   |
| --------------------------------- | ---------------------------------------------------------------- |
| `routes/auth.py`                  | Handles registration, login and logout HTTP requests.            |
| `services/auth_service.py`        | Handles password hashing, verification and authentication logic. |
| `repositories/user_repository.py` | Creates and retrieves users in PostgreSQL.                       |
| `dependencies/auth.py`            | Checks user sessions and retrieves the authenticated user.       |
| `routes/expenses.py`              | Handles expense requests and protects authenticated operations.  |
| `database.py`                     | Configures PostgreSQL connections and manages database sessions. |
| `models.py`                       | Defines User and Expense database models.                        |
| `schemas.py`                      | Validates registration, login and expense data.                  |

## Development Rules

1. Maintain separation between routes, services and repositories.
2. Use FastAPI for backend endpoints and Jinja2 for server-rendered templates.
3. Use Pydantic schemas for input validation.
4. Use SQLAlchemy models for database operations.
5. Keep authentication and authorization logic on the backend.
6. Ensure users can access only their own expenses.
7. Never store passwords in plain text.
8. Keep credentials and secret keys in environment variables.
9. Follow the existing project structure and avoid unnecessary changes.
10. Write maintainable, modular and readable code.

## Instructions for Copilot

* Inspect relevant existing files before modifying them.
* Follow the architecture and coding rules defined here.
* Place new functionality in the appropriate layer.
* Avoid duplicating existing functionality.
* Preserve existing working features when implementing changes.
* Explain significant architectural changes and list modified files.
* Run relevant tests after implementation and report the results.
