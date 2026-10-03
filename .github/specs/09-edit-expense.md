# Spec: Edit Expense

## Overview

Add a secure, authenticated edit flow that lets a logged-in user update an existing expense record in the MySQL `expenses` table. The feature should follow the project’s layered architecture and design system: a thin route validates the session and expense ownership, a service normalizes and validates the payload, a repository performs the update using parameterized SQL, and a template extends the shared base layout and matches the rest of the app.

This feature is update-only. It does not add expense deletion or a separate bulk-edit workflow. It should support the common tracked fields already defined in the schema: title, amount, category, and optional description.

## Depends on

- Step 1: Database setup — `users` and `expenses` tables exist.
- Step 2: Registration — user accounts can be created and stored securely.
- Step 3: Login and Logout — signed sessions identify the authenticated user.
- Step 5: Profile Page Backend Routes — the authenticated profile page and user-scoped data access patterns already exist.
- Step 8: Add Expense — the existing create flow and form conventions already define the expected expense fields and validation behavior.
- Existing `dependencies/auth.py`, `schemas.py`, `repositories/*`, `services/*`, `templates/base.html`, and `static/css/style.css`.

## Routes

- `GET /expenses/{expense_id}/edit` — render the authenticated edit-expense form.
  - Use the existing `get_session_user_id(request)` helper.
  - If the session user id is missing or invalid, clear a malformed `user_id` session value when present and redirect to `/login` with status `303`.
  - Fetch the target expense by `expense_id` and confirm it belongs to the logged-in user.
  - If the expense does not exist or belongs to another user, return a clear error or redirect to `/profile` without exposing internal data.
  - Keep the route name `edit_expense` and reuse `request.url_for('edit_expense', expense_id=...)` from the profile or transaction rows.
  - Render `templates/expenses/edit.html` using the shared base template.

- `POST /expenses/{expense_id}/edit` — validate and update the current authenticated user’s expense.
  - Require the session to be valid and authenticated.
  - Accept form fields: `title`, `amount`, `category`, and `description`.
  - Confirm the row exists and belongs to the current user before updating.
  - Validate the payload before modifying MySQL.
  - On success, redirect to `/profile` with status `303`.
  - On validation failure, show an inline error and preserve the submitted values in the form.
  - On a database or service failure, return a clear user-facing error without exposing internal MySQL details.

## Database changes

No new tables or schema changes are required. The existing `expenses` table already supports the needed fields:

- `user_id` foreign key to `users(id)`
- `title`, `amount`, `category`, `description`, timestamps

Repository work should use explicit parameterized SQL and remain scoped to the authenticated `user_id`. The update query must include both the expense id and the user id in the `WHERE` clause to avoid cross-user edits.

## Templates

### Create

- `templates/expenses/edit.html`
  - Extend `base.html`.
  - Use the existing Finzo layout, typography, buttons, form controls, and colors.
  - Include a heading, a form, and a validation message area.
  - Show a `Cancel` link back to `/profile`.
  - The form should include a required title, a required positive amount, a category dropdown, and a description textarea.
  - Keep the control names aligned with the route’s POST form arguments.
  - Pre-populate the form with the existing expense values when rendering the edit page.

### Modify

- `templates/profile.html` or the authenticated expense list view
  - Add an edit link or button for each expense row that routes to `/expenses/{expense_id}/edit`.
  - Keep the URL generation consistent with the current route naming and template conventions.
  - Preserve the existing profile summary and transaction layout.

- `templates/base.html`
  - Ensure navigation or page actions remain consistent when editing an expense.
  - Keep the route name stable and use the shared navbar conventions already in place.

## Files to change

- `app.py` — ensure the expenses router is already included and no placeholder route conflicts remain.
- `routes/expenses.py` — add `GET /expenses/{expense_id}/edit` and `POST /expenses/{expense_id}/edit` route handlers.
- `services/expense_service.py` — add the update service that validates and persists edited expense data.
- `repositories/expense_repository.py` — add a user-scoped update query and a fetch-by-id helper for the current user.
- `schemas.py` — add or extend an `ExpenseUpdate` model for title/amount/category/description validation.
- `templates/profile.html` or the relevant transaction block — add edit links to the current expense rows.
- `templates/expenses/edit.html` — create the edit form page.
- `static/css/style.css` — add the style rules for the Edit Expense page and any action button states introduced by the edit links.

## Files to create

- `routes/expenses.py` — if not already existing as an implementation file.
- `services/expense_service.py` — if the update logic is not already present.
- `templates/expenses/edit.html`

## New dependencies

None.

## Rules for implementation

- Follow the existing layered architecture: routes → services → repositories.
- Keep SQL in the repository layer and out of templates and route handlers.
- Use parameterized database queries; do not interpolate user input into SQL strings.
- Never allow access to another user’s expenses; all updates must be tied to the authenticated `user_id`.
- Keep the app’s MySQL usage consistent with the existing design: `PyMySQL`, explicit SQL, no ORM or migrations.
- Reuse existing CSS variables and style patterns rather than introducing a new design system.
- Preserve the project’s route naming conventions and session-based authentication flow.
- Handle empty or invalid input by returning a clear validation message instead of crashing.
- Keep route logic thin and avoid putting business logic into the template.
- Ensure the page is usable at the existing responsive breakpoints and keeps keyboard-focusable controls accessible.
- Keep the form pre-filled and preserve user input when validation fails.

## Definition of done

- [ ] An authenticated user can open an edit form for one of their own expenses from the profile or transaction list.
- [ ] A logged-out user is redirected to `/login` when visiting an edit page.
- [ ] A user cannot edit another user’s expense record.
- [ ] The form validates `title` and a positive `amount` before updating MySQL.
- [ ] The `category` field accepts user choices and defaults to a sensible value when blank.
- [ ] The form preserves user input when validation fails.
- [ ] Successful submission updates the expense for the authenticated user and redirects to `/profile`.
- [ ] The route, service, repository, and template are consistent with the existing architecture and naming patterns.
- [ ] The page matches the Finzo visual system and works at the existing responsive breakpoints.
- [ ] No unrelated app behavior is changed.
