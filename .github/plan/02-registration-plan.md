# Registration Implementation Plan

## TL;DR

Implement registration as a public auth flow in the existing FastAPI app using the layered architecture already described in the project rules. The route layer will render and process registration requests, the service layer will validate and hash the password, and the repository layer will create the new MySQL user using parameterized SQL. No schema changes are required because the project already has a `users` table from the database setup step.

---

## Findings from the Repo

- `app.py` already exposes a `GET /register` route and the project is structured around FastAPI templates and static assets.
- The core auth files exist as placeholders and should be filled in using the project’s layered pattern rather than ad hoc logic.
- The database setup step established the MySQL foundation and the users table contract, so registration should build on that instead of creating new DB objects.
- The project already uses Jinja2 templates with `base.html` and a shared CSS system, so the registration UI should follow the same conventions.
- The repository does not yet implement any user creation or lookup logic, so this feature includes the first functional auth persistence path.

---

## 1. Confirm registration requirements and input contract

Before implementation, lock down the expected submission payload and validation rules.

The registration form should accept:
- `name`
- `email`
- `password`

Validation rules:
- `name` is required and should not be empty or only whitespace
- `email` is required and must match a valid email pattern
- `password` is required and must meet a minimum length requirement
- the submitted email must be unique in the `users` table
- invalid inputs must be rejected server-side before calling the database

This validation should be mirrored in the schema layer and enforced in the service layer to avoid trusting client-side only checks.

---

## 2. Define the request/response flow

The registration flow should follow a clean request lifecycle:

1. User visits `GET /register`
2. Server renders the registration form with a public access template
3. User submits `POST /register`
4. Route validates the payload and passes it to auth service
5. Service verifies email uniqueness and password policy
6. Service hashes the password securely
7. Repository inserts the user into MySQL with a parameterized query
8. App returns either:
   - a success redirect to login or a post-registration step
   - or a rendered form with a meaningful validation error

The route layer must stay thin and delegate all business logic to the service and repository layers.

---

## 3. Implement registration validation in the schema layer

Update the schema layer in `schemas.py` to include a registration request model, or a similarly named validation model, that enforces:
- required fields
- trimmed string values
- email format validation
- password minimum length or equivalent quality criteria

The schema should not accept invalid input at the API boundary. It should also prepare consistent Python objects that the service layer can consume.

This keeps validation centralized and makes the route simpler and easier to maintain.

---

## 4. Implement the route layer in `routes/auth.py`

The auth routes should be responsible for the following:

### `GET /register`
- Render the registration template
- Pass the form context and any current error state if needed
- Keep the route public

### `POST /register`
- Accept the submitted form values
- Parse and validate with the schema
- If validation fails, re-render the form with clear error messaging
- If validation passes, call the auth service
- On success, redirect to the next logical screen
- On duplicate email or other business failure, re-render the form with a user-friendly message

Important constraints:
- no database logic inside the route
- no raw SQL or password hashing in the route
- no direct exposure of MySQL errors to the browser

---

## 5. Implement the business logic in `services/auth_service.py`

The auth service is the main registration orchestrator. Responsibilities:

- validate input against business rules
- check whether the email already exists
- normalize or sanitize fields if necessary
- hash the password using the secure password hashing method adopted by the project
- call the repository insert function
- return a clear success or failure result to the route

This is the correct place to enforce the rule that passwords are never stored as plain text.

The service should also handle duplicate-email and validation-related exceptions in a controlled way so the route can present the right user-facing response.

---

## 6. Implement the repository logic in `repositories/user_repository.py`

The repository layer will own all user persistence actions.

Planned methods:
- `get_user_by_email(email: str)`
- `create_user(name: str, email: str, password_hash: str)`

Repository responsibilities:
- query the existing `users` table
- check for duplicate email addresses
- insert the new user using a parameterized MySQL query
- return the newly created user or a database result object
- keep all SQL logic explicit and direct with PyMySQL

The repository must not use SQLAlchemy or any ORM abstraction. All queries should be parameterized and safe.

---

## 7. Align with the existing users table contract

Before writing the final repository queries, confirm the schema already defined during Step 1.

Expected characteristics of the `users` table:
- primary key column
- unique email column
- required name field
- required password-related field for the hashed password
- proper MySQL column types and not-null constraints

The registration logic must insert only into valid columns and respect the unique email constraint. If the DB uses a password hash column name like `password_hash`, the repository and service should consistently use that name.

This ensures that registration does not assume a schema that does not exist.

---

## 8. Update the registration template and UI

The markup in `templates/register.html` already provides the structure for the form. The plan is to complete the end-to-end UX as follows:

- confirm the form action points to the registration endpoint
- maintain the current auth-style layout and naming
- show validation and duplicate-email errors visibly
- keep password field semantics clear and accessible
- ensure the success or error message flow fits the app’s design language

The page should still extend the design pattern established in `base.html` and use the existing CSS variable conventions rather than introducing unrelated styling.

---

## 9. Update shared styles if needed

Check the existing CSS under `static` and only add styling changes required for registration-specific states.

This may include:
- form error styles
- success banner styles
- submit button states
- layout polish required for auth forms

The styling should remain consistent with the current Finzo design system and avoid introducing unrelated visual noise.

---

## 10. Add graceful error handling

The final implementation must handle several outcomes cleanly:

- invalid form payload
- duplicate email
- database connectivity errors
- unexpected repository failures

User-facing behavior:
- show simple, actionable messages
- avoid raw DB exception dumps in the browser
- re-render the registration form with error context when appropriate

This is important because the registration step is the first real end-user authentication interaction in the app.

---

## 11. Wire the flow into the app entrypoint

The app entrypoint in `app.py` should remain the central place for FastAPI route registration and startup behavior. The registration implementation should not create duplicate route definitions or bypass the existing app architecture.

The focus is to ensure:
- `GET /register` and `POST /register` are available
- the route is public
- the auth logic lives in the correct modules
- app startup behavior remains untouched aside from the auth route wiring

---

## 12. Verification checklist

The implementation is considered complete only when the following are satisfied:

- `GET /register` renders a working form page
- the form includes the required fields for name, email, and password
- a valid submission creates a user record in the MySQL `users` table
- a duplicate email is blocked with a clear message
- invalid input is blocked before hitting the database
- the stored password is hashed, not plain text
- the code remains in the proper route/service/repository structure
- the feature does not interfere with the database setup or unrelated launch routes

---

## Scope boundaries

### In scope
- public registration page
- validation and business rules
- password hashing
- parameterized MySQL insert
- duplicate email handling
- user-facing error states
- template and styling updates for auth flow

### Out of scope
- login flow
- logout flow
- session logic
- profile pages
- expense tracking features
- any database schema redesign
- SQLAlchemy or ORM introduction
- Alembic or migration setup

---

## Implementation order

1. Confirm schema contract and database assumptions
2. Add registration validation schema
3. Build repository lookup and create methods
4. Build service registration logic with hashing and duplicate checks
5. Implement route GET/POST handling
6. Update templates and styles for registration UX
7. Verify with targeted app-based checks

This keeps the work structured and ensures the layers remain clean and testable.
