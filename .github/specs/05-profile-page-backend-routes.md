# Spec: Profile Page Backend Routes

## Overview

Connect the profile page created in Step 04 to the authenticated user's real account and expense data. The existing `/profile` page remains a server-rendered Jinja2 page; its sample data is replaced by data fetched from MySQL through the repository and service layers.

This step is read-only. It does not add profile editing, expense CRUD, or a JSON API.

## Depends on

- Step 1: Database setup — the MySQL `users` and `expenses` tables exist.
- Step 2: Registration — user records have the expected fields.
- Step 3: Login + Logout — signed sessions store the authenticated `user_id`.
- Step 4: Profile Page Design — `templates/profile.html` and its context shape exist.

## Routes

- `GET /profile` — render the authenticated user's profile and expense summary.
  - Keep the existing route name `profile` so template links using `request.url_for('profile')` continue to work.
  - If the request has no valid session user ID, clear any malformed session and redirect to `/login` with status `303`.
  - If the session contains a valid user ID but the account no longer exists, clear the session and redirect to `/login` with status `303`.
  - On success, render `templates/profile.html` using the real-data context returned by the profile service.
  - If required profile data cannot be loaded because MySQL is unavailable, log the failure and return a generic `503` response. Do not expose database details or silently substitute sample data.

No additional routes are introduced in this step.

## Data requirements

Build the existing template context keys (`user`, `summary`, `transactions`, and `category_breakdown`) from repositories and service formatting helpers:

- `user`: `id`, `name`, `email`, initials, and member-since display value derived from `users.created_at`.
- `summary`: current-calendar-month total spent, transaction count, top category, display period, and `is_sample: false`.
- `transactions`: up to five most recent expenses for the authenticated user, ordered newest first. Include the transaction date, display description/title, category text and CSS class, and formatted amount.
- `category_breakdown`: current-calendar-month totals grouped by the expense category, with display amounts, category CSS classes, and percentage shares.

For the monthly summary and category breakdown, use the current calendar month in the application's configured timezone. Use a half-open timestamp range (`start <= created_at < next_month_start`) so the month boundary is unambiguous. The summary total must be derived from the same month and user scope as its transaction count, top category, and breakdown. Resolve tied top categories deterministically (alphabetically by category name).

When there are no expenses in the current month, return zero total and count, an empty top-category value, and an empty breakdown. When there are no expenses at all, return an empty recent-transactions list. Do not fabricate example rows or categories.

Keep the context's existing presentation contract so the Step 04 template does not need a redesign. Formatting and derived values belong in `services/profile_service.py`, not in the route, SQL result assembly, or Jinja template. Preserve the established Finzo conventions: Indian-grouped rupee amounts, `DD Mon YYYY` dates, `Month YYYY` member-since values, safe initials fallback for a blank name, and a neutral CSS class for unrecognized category text.

## Database and security

- Use MySQL through the existing PyMySQL database helper.
- Put user and expense SQL in repositories; keep SQL out of `app.py`, route handlers, services, and templates.
- Add `get_user_by_id` to the user repository. Select only the fields needed for the profile (`id`, `name`, `email`, `created_at`); never return `password_hash` for profile display.
- Add an expense repository for the profile's recent expenses and current-month aggregates.
- Parameterize every user ID and date bound.
- Every expense query must filter by the authenticated user's `user_id`; never return another account's transactions or aggregates.
- Do not change the existing database schema or use an ORM, migration framework, or new dependency.
- A missing user is a normal stale-session case; distinguish it from database failures.

## Files to change

- `app.py` — include the profile router and remove the existing inline `/profile` handler so only one route is registered.
- `routes/profile.py` — create the thin authenticated page route, preserving route name `profile`.
- `services/profile_service.py` — replace Step 04 sample data with repository-backed context building and formatting.
- `repositories/user_repository.py` — add safe profile lookup by user ID.
- `repositories/expense_repository.py` — add user-scoped recent-expense and monthly aggregate queries.
- `tests/test_profile.py` — replace sample-data assumptions and cover the real-data service/route behavior using repository/database stubs.

Modify `templates/profile.html` only if its current context usage is incompatible with the Step 04 context contract. Do not redesign it as part of this step.

## New dependencies

None.

## Rules for implementation

- Follow the existing FastAPI, Jinja2, service, repository, and dependency patterns.
- Reuse `get_session_user_id(request)` for the page's existing signed-session authentication. Do not create a second authentication mechanism.
- Keep the route thin: obtain the session user ID, request the profile context from the service, handle missing-user and unavailable-data outcomes, and render the template.
- Use parameterized MySQL queries and the existing database helper.
- Preserve the `/profile` URL and route name, the existing template context keys, and authenticated navigation behavior.
- Do not keep sample profile or expense data in the live request path.
- Do not add update/delete actions, forms, or API endpoints.
- Keep user-visible database errors generic and log operational failures; do not silently present stale or sample values as current data.
- Keep all secrets and database connection details in environment-based configuration.

## Definition of done

- [ ] `GET /profile` redirects anonymous and malformed-session visitors to `/login` with status `303`.
- [ ] A valid session for a deleted user is cleared and redirected to `/login` with status `303`.
- [ ] A valid authenticated user receives HTTP `200` and their own profile data.
- [ ] The profile lookup does not select or expose the user's password hash.
- [ ] Summary amount, count, top category, and breakdown use only the authenticated user's expenses for the current calendar month.
- [ ] Recent transactions contain no more than five of the authenticated user's newest expenses and are ordered newest first.
- [ ] Every repository query is parameterized and every expense query is scoped by `user_id`.
- [ ] Empty-expense and zero-total cases render valid zero/empty values without division errors or sample-data fallbacks.
- [ ] Formatting, category fallback, initials, and percentage behavior remain compatible with the profile template.
- [ ] Database failures produce a logged, generic `503` response without leaking SQL, credentials, or raw database errors.
- [ ] Tests cover authorization, stale sessions, user scoping, monthly date boundaries, ordering/limit, missing/empty data, and database failure handling.
- [ ] The existing profile template and authenticated navigation continue to work without a redesign.
- [ ] No schema changes, new dependencies, SQLAlchemy, Alembic, or additional routes are introduced.
