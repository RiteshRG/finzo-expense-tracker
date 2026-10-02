# Login and Logout Implementation Plan

## TL;DR

Complete authentication using the existing FastAPI auth routes, service, repository, login template, and shared layout. Look up users by normalized email, verify Werkzeug password hashes, and establish a signed session containing only the user identifier. Logout clears that session through a POST route. No database schema changes are required.

---

## Findings from the Repo

- `app.py` registers the auth router and currently also renders `/login` separately. Resolve route ownership to avoid duplicate `/login` definitions.
- `routes/auth.py` contains registration routes; extend the same router for login and logout.
- `services/auth_service.py` handles registration and password hashing; add credential verification without breaking registration.
- `repositories/user_repository.py` retrieves users by email. Ensure the service can access the hash for verification, but never pass it to templates or sessions.
- `schemas.py` defines `UserLogin`, which should be used for server-side validation.
- `templates/login.html` already provides email/password inputs and an error display slot.
- `templates/base.html` always shows anonymous login/register links; make navigation depend on authentication state.
- `dependencies/auth.py` is an empty placeholder and is the appropriate location for a reusable session-authenticated-user dependency.
- The project uses FastAPI, Jinja2, MySQL/PyMySQL, and Werkzeug. Check whether `itsdangerous` is declared and add it to `requirements.txt` if missing; Starlette requires it for signed sessions.

---

## 1. Define and validate login input

Use `UserLogin` from `schemas.py` as the authoritative request model.

- Require email and password on the server regardless of HTML `required` attributes.
- Validate email format and normalize it consistently with registration.
- Do not trim or otherwise modify the password before verification.
- Re-render the form with an actionable error for missing or malformed fields instead of returning an unhandled validation response.
- Preserve the normalized email after errors, but never repopulate the password.

## 2. Extend repository login lookup

Reuse `get_user_by_email` from `repositories/user_repository.py` or adjust it narrowly if the current return shape is insufficient.

- Use a parameterized MySQL query against the existing `users` table.
- Normalize lookup email consistently with registration.
- Return only fields needed by the service, including id, email, and password hash.
- Keep SQL and database access in the repository/database layer.
- Do not add schema changes, ORM code, or migration tooling.

## 3. Implement credential verification in the auth service

Extend `services/auth_service.py` while preserving `register_user`.

- Retrieve the user by normalized email through the repository.
- Treat unknown email and incorrect password as the same authentication failure.
- Verify the submitted password with Werkzeug's hash verification function.
- Return a minimal authenticated-user representation (for example, id and display name), not the password hash.
- Distinguish expected invalid credentials from unexpected database/system errors internally. Do not expose raw database details or treat infrastructure failures as successful authentication.

## 4. Configure signed session middleware safely

Update app configuration to support Starlette/FastAPI signed sessions.

- Add `SessionMiddleware` once to the FastAPI app.
- Read its signing secret from a required environment variable such as `SESSION_SECRET_KEY`; do not commit a fallback secret.
- Fail clearly when the required signing secret is absent rather than creating insecure sessions.
- Configure `HttpOnly` and an explicit `SameSite` policy. Enable `Secure` for HTTPS deployments while keeping local HTTP development usable.
- Declare `itsdangerous` in `requirements.txt` if it is not already present.

## 5. Implement public login routes

Add login handling in `routes/auth.py`.

### `GET /login`
- Render `login.html` as a public page with empty error/email context as needed.

### `POST /login`
- Accept form fields and validate them through `UserLogin`.
- Call the auth service to verify credentials.
- On invalid credentials, show one generic message for unknown email and incorrect password.
- On database/system failure, show a non-technical service error and retain server-side diagnostics through standard logging/error handling.
- On success, clear stale authentication state, store only the minimum user identifier in the signed session, and redirect with HTTP 303 to the agreed destination.

Keep existing registration behavior intact.

## 6. Implement logout as a state-changing POST route

Add `POST /logout` to the auth router.

- Require the authenticated-user dependency, or explicitly make session clearing idempotent for expired/absent sessions according to the chosen route policy.
- Remove the authentication identifier and related auth session data.
- Redirect to `/login` with HTTP 303.
- Do not access MySQL during logout.
- Do not implement logout as GET.

## 7. Add the authenticated-user dependency

Implement `dependencies/auth.py` as the shared session reader.

- Read the user identifier from the signed request session.
- Resolve the current user through the repository only when a route needs a user object; otherwise expose the minimal identifier.
- Reject absent, malformed, or stale session identifiers using the application's standard unauthenticated behavior.
- Never accept identity or authorization state from untrusted form/query parameters.
- Do not apply this dependency to public login or registration routes.

Keep it reusable for future authenticated pages, but do not protect unrelated routes in this task.

## 8. Update login template and shared navigation

### `templates/login.html`
- Preserve `base.html` inheritance and existing auth styling.
- Associate error feedback with an accessible alert role.
- Preserve the email value after failed login using escaped template context.
- Never echo the password back into the page.

### `templates/base.html`
- Keep login and registration links visible to anonymous visitors.
- For authenticated users, show an appropriate signed-in indicator if available and a POST logout form.
- Use request/session context for presentation only; backend dependencies remain authoritative for access control.
- Preserve existing layout, footer, CSS variables, and unrelated route behavior.

## 9. Handle errors without leaking internals

Explicitly account for:

- Missing email or password
- Malformed email
- Unknown email
- Incorrect password
- Database connectivity/query failure
- Expired, absent, or malformed session
- Logout with an already-cleared session

Unknown email and incorrect password must be indistinguishable to users. Database errors must be handled/logged server-side, not shown verbatim. Login failures must never create a session; logout must clear session state even when the database is unavailable. Avoid broad silent exception swallowing or success-shaped fallbacks.

## 10. Verification and tests

Add focused tests covering:

1. `GET /login` returns the sign-in page successfully.
2. Valid credentials create a session with the expected user id and return a 303 redirect.
3. Incorrect password does not create a session and shows the generic credential message.
4. Unknown email returns the same user-facing message as incorrect password.
5. Invalid or missing form input renders a clear login form error.
6. Database failure does not reveal raw exception details and does not create a session.
7. `POST /logout` clears session state and returns a 303 redirect without database access.
8. Authenticated navigation includes a POST logout control; anonymous navigation retains login/register links.
9. Registration continues to work, including its existing form and password-hashing behavior.
10. Existing database-layer tests continue to pass.

Run focused tests first, then the existing test suite if the targeted results are clean.

---

## Implementation order

1. Confirm the user lookup return shape and session middleware dependency.
2. Add or adjust login schema normalization and required-field handling.
3. Extend repository lookup only as needed for password verification.
4. Implement service-level credential verification.
5. Implement the reusable auth dependency.
6. Wire signed session middleware with environment-backed configuration.
7. Add POST login and POST logout routes; resolve duplicate `/login` route ownership in `app.py`.
8. Update login feedback and conditional shared navigation.
9. Add focused route/service/session tests.
10. Run targeted tests and verify registration and database setup remain intact.

---

## Scope boundaries

### In scope
- Login form and credential verification
- Signed session creation and reading
- POST logout and session clearing
- Authenticated navigation state
- Input validation, error feedback, and tests

### Out of scope
- Registration redesign
- User profile or dashboard implementation
- Protecting expense routes or adding expense features
- Database schema changes
- Password reset, email verification, remember-me, or multi-factor authentication
- SQLAlchemy, Alembic, or another ORM/migration framework
