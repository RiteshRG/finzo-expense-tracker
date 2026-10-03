# Spec: Add Expense

## Overview

Add a secure, authenticated form that lets a logged-in user create a new expense record in the MySQL `expenses` table. The feature should follow the existing Finzo architecture and design system: a thin route that checks the session, a service that validates payloads, a repository that inserts the row with parameterized SQL, and a template that extends the shared base layout and matches the rest of the app.

This feature is create-only. It does not add expense editing, deletion, or update flows. It should support the common tracked fields already defined in the schema: title, amount, category, and optional description.

## Depends on

- Step 1: Database setup — `users` and `expenses` tables exist.
- Step 2: Registration — user accounts can be created and stored securely.
- Step 3: Login and Logout — signed sessions identify the authenticated user.
- Step 5: Profile Page Backend Routes — the authenticated profile page and user-scoped data access patterns already exist.
- Existing `dependencies/auth.py`, `schemas.py`, `repositories/*`, `services/*`, `templates/base.html`, and `static/css/style.css`.

## Routes

- `GET /expenses/add` — render the authenticated add-expense form.
  - Use the existing `get_session_user_id(request)` helper.
  - If the session user id is missing or invalid, clear a malformed `user_id` session value when present and redirect to `/login` with status `303`.
  - Keep the route name `add_expense` to support `request.url_for('add_expense')` links from the authenticated navigation.
  - Render `templates/expenses/add.html` using the shared base template.

- `POST /expenses/add` — validate and create a new expense for the current authenticated user.
  - Require the session to be valid and authenticated.
  - Accept form fields: `title`, `amount`, `category`, and `description`.
  - Validate the payload before inserting into MySQL.
  - On success, redirect to `/profile` with status `303`.
  - On validation failure, show an inline error and preserve the submitted values in the form.
  - On a database or service failure, return a clear user-facing error without exposing internal MySQL details.

## Database changes

No new tables or schema changes are required. The existing `expenses` table already supports the needed fields:

- `user_id` foreign key to `users(id)`
- `title`, `amount`, `category`, `description`, timestamps

Repository work should use explicit parameterized SQL and remain scoped to the authenticated `user_id`.

## Templates

### Create

- `templates/expenses/add.html`
  - Extend `base.html`.
  - Use the existing Finzo layout, typography, buttons, form controls, and colors.
  - Include a heading, a form, and a validation message area.
  - Show a `Cancel` link back to `/profile`.
  - The form should include a required title, a required positive amount, a category dropdown, and a description textarea.
  - Keep the control names aligned with the route's POST form arguments.

### Modify

- `templates/base.html`
  - Add an authenticated navigation link for “Add expense”.
  - Keep the route name stable and use the shared navbar convention.
  - Mark the link as active when the current page is `/expenses/add`.
  - Preserve the existing Profile, Analytics, and sign-out links.

## Files to change

- `app.py` — include the dedicated expenses router and remove the placeholder expense routes if they remain.
- `routes/expenses.py` — add the `GET /expenses/add` and `POST /expenses/add` route handlers.
- `services/expense_service.py` — create the service that validates and converts submitted expense data.
- `repositories/expense_repository.py` — add insert logic scoped to the current user.
- `schemas.py` — add an `ExpenseCreate` model for title/amount/category/description validation.
- `templates/base.html` — add the nav entry to access the new page.
- `static/css/style.css` — add the style rules for the Add Expense page and the active nav state.

## Files to create

- `routes/expenses.py` — if not already existing as an implementation file.
- `services/expense_service.py`
- `templates/expenses/add.html`

## New dependencies

None.

## Rules for implementation

- Follow the existing layered architecture: routes → services → repositories.
- Keep SQL in the repository layer and out of templates and route handlers.
- Use parameterized database queries; do not interpolate user input into SQL strings.
- Never allow access to another user’s expenses; all insertions must be tied to the authenticated `user_id`.
- Keep the app’s MySQL usage consistent with the existing design: `PyMySQL`, explicit SQL, no ORM or migrations.
- Reuse existing CSS variables and style patterns rather than introducing a new design system.
- Preserve the project’s route naming conventions and session-based authentication flow.
- Handle empty or invalid input by returning a clear validation message instead of crashing.
- Keep route logic thin and avoid putting business logic into the template.
- Ensure the page is usable at the existing responsive breakpoints and keeps keyboard-focusable controls accessible.

## Definition of done

- [ ] An authenticated user can open the Add expense form from the main navigation.
- [ ] A logged-out user is redirected to `/login` when visiting `/expenses/add`.
- [ ] The form validates `title` and a positive `amount` before inserting into MySQL.
- [ ] The `category` field accepts user choices and defaults to a sensible value when blank.
- [ ] The form preserves user input when validation fails.
- [ ] Successful submission creates the expense for the authenticated user and redirects to `/profile`.
- [ ] The route, service, repository, and template are consistent with the existing architecture and naming patterns.
- [ ] The page matches the Finzo visual system and works at the existing responsive breakpoints.
- [ ] No unrelated app behavior is changed.
