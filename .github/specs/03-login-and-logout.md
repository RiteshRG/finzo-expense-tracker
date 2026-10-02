# Spec: Login and Logout

## Overview
Login and logout complete Finzo's initial authentication flow by allowing registered users to authenticate with their email and password, retain their authenticated state across requests, and securely end that state when they log out. Login verifies stored Werkzeug password hashes without exposing whether an email or password was incorrect; logout clears the server-side request session and returns the user to a public page.

## Depends on
- Step 1: Database setup and MySQL users table
- Step 2: Registration, including normalized email addresses and Werkzeug password hashes
- Existing FastAPI app, auth templates, and shared layout

## Routes
- `GET /login` — display the sign-in form — public
- `POST /login` — validate credentials, establish an authenticated session, and redirect to the next appropriate page — public
- `POST /logout` — clear the authenticated session and redirect to the login page — logged-in

## Database changes
No database changes. Login retrieves the account by its normalized email from the existing `users` table and verifies the submitted password against the stored `password_hash`. Logout does not access the database.

## Templates
- **Create:** None
- **Modify:** `templates/login.html` — support login error feedback and preserve a normalized email value after an unsuccessful attempt; do not repopulate the password
- **Modify:** `templates/base.html` — show authentication-appropriate navigation and provide a POST logout form for logged-in users while retaining login/register links for visitors

## Files to change
`app.py`, `routes/auth.py`, `services/auth_service.py`, `repositories/user_repository.py`, `dependencies/auth.py`, `templates/login.html`, `templates/base.html`, `requirements.txt`

## Files to create
None

## New dependencies
Add `itsdangerous` explicitly if it is not already declared, for Starlette's signed session middleware.

## Rules for implementation
- FastAPI for backend routes
- MySQL with PyMySQL
- No SQLAlchemy or ORMs
- No Alembic or migration framework
- Parameterised queries only
- Passwords hashed with Werkzeug where applicable; verify with Werkzeug's password-hash verification helper
- Secrets and database credentials must use environment variables; configure the session signing key from a required environment variable and do not use a committed fallback
- Follow the existing routes/services/repositories structure
- Use CSS variables and follow the existing UI conventions
- All templates extend `base.html` if the project uses that layout
- Do not introduce unrelated features
- Use a generic user-facing login error for unknown emails and incorrect passwords
- Store only the minimum user identifier needed in the signed session; never place passwords or password hashes in the session
- Set session-cookie security attributes appropriately, including `HttpOnly` and `SameSite`; enable `Secure` when served over HTTPS
- Logout must use POST because it changes authentication state

## Definition of done
- [ ] `GET /login` renders the existing sign-in form and remains accessible without authentication.
- [ ] `POST /login` accepts valid form data, normalizes the email consistently with registration, and verifies the submitted password against the stored Werkzeug hash.
- [ ] Successful login establishes a signed authenticated session and redirects with a `303` response to the agreed post-login destination.
- [ ] Unknown email and incorrect password produce the same user-facing error and do not disclose account existence.
- [ ] Malformed or missing login fields are handled with a clear form error rather than an unhandled exception.
- [ ] Database lookup uses the existing repository and parameterized SQL; database failures are not exposed as raw MySQL errors.
- [ ] Session configuration requires an environment-provided secret and does not contain a hard-coded signing key.
- [ ] Authenticated navigation offers a POST logout action; public navigation continues to expose login and registration links.
- [ ] `POST /logout` clears the session and redirects to the login page; logging out does not depend on database availability.
- [ ] Tests cover successful login, incorrect password, unknown email, malformed input, session creation, and logout/session clearing.
- [ ] Existing registration and unrelated routes continue to work without database schema changes.
