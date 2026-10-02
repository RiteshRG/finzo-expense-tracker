# Spec: Registration

## Overview
Registration is the first user-facing authentication workflow in the Finzo roadmap. It allows a new user to create an account with a name, email, and password, validates the submitted data, stores the account securely, and prepares the system for the subsequent login and expense-tracking features.

## Depends on
- Step 1: Database setup and MySQL foundation
- Existing landing page and auth page shell in the app

## Routes
- `GET /register` — display the account creation form — public
- `POST /register` — validate form data, hash the password, insert the new user, and redirect to the next appropriate screen — public

## Database changes
No database changes. Registration uses the existing `users` table created during the database setup step, including the unique email constraint and parameterized insert query required for new account creation.

## Templates
- **Create:** None
- **Modify:** `templates/register.html` — add the registration form submission flow, validation messages, password requirements, and success/error handling
- **Modify:** `templates/base.html` — ensure any shared auth styling or CTA adjustments remain consistent with the Finzo UI

## Files to change
`app.py`, `schemas.py`, `routes/auth.py`, `services/auth_service.py`, `repositories/user_repository.py`, `templates/register.html`, `static/css/style.css`

## Files to create
`routes/auth.py`, `services/auth_service.py`, `repositories/user_repository.py`

## New dependencies
No new dependencies.

## Rules for implementation
- FastAPI for backend routes
- MySQL with PyMySQL
- No SQLAlchemy or ORMs
- No Alembic or migration framework
- Parameterised queries only
- Passwords hashed with Werkzeug where applicable
- Secrets and database credentials must use environment variables
- Follow the existing routes/services/repositories structure
- Use CSS variables and follow the existing UI conventions
- All templates extend `base.html` if the project uses that layout
- Do not introduce unrelated features

## Definition of done
- [ ] `GET /register` renders a valid registration form with the required fields and styling.
- [ ] `POST /register` validates name, email, and password requirements before creating a user.
- [ ] Duplicate email addresses are rejected cleanly with a user-facing error.
- [ ] Passwords are stored as hashed values and not in plain text.
- [ ] The new user is created through a parameterized MySQL insert using the existing `users` table.
- [ ] Successful registration redirects the user to a logical next step, such as login or a minimal post-registration view.
- [ ] Registration does not interfere with the database setup from Step 1 or with unrelated expense-tracking functionality.
