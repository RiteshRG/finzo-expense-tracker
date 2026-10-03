# Spec: Delete Expense

## Overview

Add a secure, authenticated flow that lets a logged-in user permanently delete one of their own expense records from the MySQL `expenses` table. Follow the existing layered architecture: the route checks the session, the service coordinates the deletion, and the repository executes a parameterized, user-scoped `DELETE`.

Expose the action beside Edit in the profile transaction list. Require a user confirmation before submitting the delete form, and never perform deletion through a GET request. This feature is single-expense deletion only; it does not add bulk deletion, soft deletion, or an undo workflow.

## Depends on

- Step 1: Database setup — the `expenses` table exists.
- Step 2: Registration — user accounts can be created and stored securely.
- Step 3: Login and Logout — signed sessions identify the authenticated user.
- Step 5: Profile Page Backend Routes — the authenticated profile and user-scoped transaction list exist.
- Step 8: Add Expense — expense records can be created.
- Step 9: Edit Expense — expense ownership and transaction-row action patterns are established.
- Existing `dependencies/auth.py`, `repositories/expense_repository.py`, `services/expense_service.py`, `templates/profile.html`, and `static/css/style.css`.

## Routes

- `POST /expenses/{expense_id}/delete` — delete one expense owned by the authenticated user.
  - Keep the route name `delete_expense` for URL generation in the profile transaction list.
  - Use the existing `get_session_user_id(request)` helper.
  - If the session user id is missing or invalid, clear a malformed `user_id` session value when present and redirect to `/login` with status `303`.
  - Pass both `expense_id` and the authenticated `user_id` through the service and repository layers. Never trust a user id supplied by the form.
  - If no row is deleted because the expense does not exist or belongs to another user, redirect to `/profile` without revealing which condition occurred.
  - On success, redirect to `/profile` with status `303`.
  - On a database or service failure, log the error and return a clear generic failure response without exposing internal MySQL details; do not report success.

## Database changes

No new tables, columns, or schema changes are required.

Add a repository operation that issues a parameterized `DELETE FROM expenses WHERE id = %s AND user_id = %s`. Return an explicit result indicating whether exactly one row was deleted so the service and route can distinguish success from a missing or unauthorized expense.

## Templates

### Create

None. Deletion uses the existing profile transaction list and does not need a separate page.

### Modify

- `templates/profile.html`
  - Add a Delete form/button beside the existing Edit link for each transaction.
  - Submit to `request.url_for('delete_expense', expense_id=transaction.id)` using `POST`.
  - Ask for confirmation before submission using the app's existing JavaScript conventions; do not use a GET link for the destructive action.
  - Keep the action controls keyboard accessible and preserve the current table layout and empty state.

- `static/js/main.js` and `static/css/style.css`
  - Update only if needed to wire the confirmation interaction and style the delete button consistently with the existing action controls.
  - Reuse existing design tokens and patterns; do not add a JavaScript or CSS framework.

## Files to change

- `routes/expenses.py` — add the authenticated POST delete route and handle service outcomes.
- `services/expense_service.py` — add deletion coordination and a clear error/result contract.
- `repositories/expense_repository.py` — add a parameterized delete scoped to both expense id and authenticated user id.
- `templates/profile.html` — add a confirmed POST delete control for each transaction.
- `static/js/main.js` — only if the existing JavaScript does not already provide the confirmation interaction.
- `static/css/style.css` — only if the existing action styles do not cover the delete control.

## Files to create

- `tests/test_10-delete-expense.py` — cover authentication, ownership isolation, successful deletion, missing expenses, and repository scoping using the project's existing test patterns.

## New dependencies

None.

## Rules for implementation

- Follow the existing layered architecture: routes → services → repositories.
- Keep SQL in the repository layer and out of routes and templates.
- Use parameterized SQL; do not interpolate user input into query strings.
- Include both the expense id and authenticated user id in the `DELETE` condition so one user cannot delete another user's expense.
- Do not accept ownership identifiers from submitted form fields.
- Do not mutate data in a GET route; the delete form must submit using POST.
- Keep authentication behavior consistent with the existing expense routes.
- Treat nonexistent and other-user expenses identically in user-facing responses.
- Log database or service failures and show a generic failure rather than exposing internal details or silently redirecting as though deletion succeeded.
- Reuse the current profile action layout, shared CSS variables, and vanilla JavaScript conventions.
- Preserve existing create, edit, profile filtering, and transaction-list behavior.

## Definition of done

- [ ] An authenticated user can delete one of their own expenses from the profile transaction list after confirming the action.
- [ ] The delete control submits a POST request and no GET request can delete an expense.
- [ ] A logged-out user is redirected to `/login`.
- [ ] A user cannot delete another user's expense, including by changing the expense id in the request.
- [ ] Missing and unauthorized expense ids do not reveal whether another user's record exists.
- [ ] Successful deletion removes exactly the selected expense and redirects to `/profile`.
- [ ] A database or service failure is logged and produces an explicit generic failure response, not a success-shaped redirect.
- [ ] Repository SQL is parameterized and constrained by both expense id and authenticated user id.
- [ ] The profile transaction list remains usable, accessible, and correctly displays its empty state after deletion.
- [ ] Automated tests cover the route and repository/service behavior without requiring destructive operations against a live user database.
- [ ] No schema changes, new dependencies, or unrelated app behavior changes are introduced.
