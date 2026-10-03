# Spec: Profile Page Date Filter

## Overview

Add date filtering to the authenticated profile page. Users can select a clickable calendar-month preset or enter a custom date range. The effective range applies consistently to the spending summary, transaction count, top category, category breakdown, and transaction table.

The filter is submitted as query parameters so a selected range can be bookmarked or shared. With no dates supplied, the page defaults to the current UTC calendar month, preserving the existing profile page's default summary period. Quick presets are “This month,” “Last 3 months,” and “Last 6 months”; multi-month presets include the current calendar month and the preceding complete calendar months. The custom date inputs remain available for any inclusive start and end dates. The transaction table shows every matching transaction in newest-first order.

This feature is read-only. It does not add expense creation, editing, deletion, or profile editing.

## Depends on

- Step 1: Database setup — the MySQL `users` and `expenses` tables exist.
- Step 2: Registration — user records have the expected fields.
- Step 3: Login + Logout — signed sessions store the authenticated `user_id`.
- Step 4: Profile Page Design — the profile template, styles, and context contract exist.
- Step 5: Profile Page Backend Routes — the profile page is backed by the authenticated user's MySQL data.

## Routes

- `GET /profile` — render the signed-in user's profile for the requested date range.
  - Keep the existing route name `profile` and URL.
  - Accept optional `start_date` and `end_date` query parameters in ISO `YYYY-MM-DD` format.
  - If neither parameter is supplied, use the first and last day of the current calendar month.
  - If one parameter is omitted, default that bound to the corresponding current-calendar-month boundary.
  - Keep the existing UTC behavior: the profile service uses UTC calendar boundaries and the MySQL session timezone is UTC. Do not add or infer a different application timezone.
  - Treat the selected dates as inclusive UTC calendar dates. Convert them to a half-open database interval: `created_at >= start_datetime` and `created_at < day_after_end_datetime`.
  - If `start_date` is after `end_date`, return a clear client error (`400`) without querying expense data. A malformed date is rejected by FastAPI request validation (`422`).
  - Preserve the existing authentication behavior: anonymous or malformed sessions are cleared as needed and redirected to `/login` with status `303`; a deleted account clears the session and redirects in the same way.
  - If MySQL data cannot be loaded, log the failure and return the existing generic `503` response. Do not expose database details or fall back to sample data.

## Database changes

No schema changes. The existing `users` and `expenses` tables are sufficient.

Update the expense repository's profile queries to accept the resolved range:

- Fetch every matching transaction for the authenticated user, ordered newest first with a deterministic ID tie-breaker.
- Aggregate all matching expenses by category, including each category's amount and transaction count.
- Apply the same user ID and half-open date bounds to both queries.
- Parameterize all user IDs and date bounds.

## Templates

### Create

None.

### Modify

- `templates/profile.html`
  - Add accessible clickable GET links for the “This month,” “Last 3 months,” and “Last 6 months” presets. Each link passes the corresponding `start_date` and `end_date` query parameters.
  - Indicate the active preset accessibly and visually.
  - Add a GET form with labelled native date inputs for custom start and end dates and an apply button. Populate the controls with the effective dates used for the page, including defaults.
  - Identify the effective range in both the spending overview and transaction section; the transaction section must clearly indicate that all transactions in that range are shown.
  - Keep the existing profile, summary, transaction, and category-breakdown structure and empty states. Display the empty transaction and category states when the selected range has no matching expenses.

## Files to change

- `routes/profile.py` — accept and validate date query parameters while preserving the existing auth, stale-session, and database-error behavior.
- `services/profile_service.py` — resolve default dates, validate range ordering, pass the same effective bounds to the repository queries, and build the selected-range summary/context. Keep date and currency formatting and category/percentage calculations in the service.
- `repositories/expense_repository.py` — apply the parameterized user-scoped range to the recent-transaction and category-aggregate queries.
- `templates/profile.html` — add preset links and the custom date form, display the active range and all matching transaction rows.
- `static/css/style.css` — style the presets and custom filter with existing Finzo tokens and responsive breakpoints; do not add inline styles or a second stylesheet.
- `tests/test_profile.py` — cover defaults, presets, custom ranges, range validation, and consistent filtering across all profile spending sections.
- `tests/test_auth_login.py` — keep existing profile context stubs compatible with the date-filter context.

## Files to create

None.

## New dependencies

None.

## Rules for implementation

- Follow the existing FastAPI, Jinja2, service, repository, and session-authentication patterns.
- Keep SQL in repositories, database access out of routes and templates, and presentation formatting out of Jinja.
- Do not duplicate the `/profile` route or change its route name.
- Use the same inclusive selected dates and user scope for the summary total, transaction count, top category, category breakdown, and recent transactions.
- Keep the summary, breakdown, and transaction table consistent with all matching expenses in the range.
- Show every matching transaction in the selected range; do not add an arbitrary row limit or pagination in this feature.
- Preserve newest-first transaction order with deterministic ID tie-breaking.
- Build preset dates from UTC calendar-month boundaries. “Last 3 months” and “Last 6 months” include the current UTC month plus the two or five preceding complete calendar months respectively.
- The preset links and custom date form must use the same query parameter names and date-range behavior.
- Keep the selected date range visible in both the spending overview and transaction section, and identify the currently active preset.
- For an empty range, return a zero total and transaction count, an empty top-category value, an empty breakdown, and no transaction rows; do not fabricate sample data.
- Resolve tied top categories deterministically, and keep category fallback, currency formatting, date formatting, and percentage behavior compatible with the current template.
- Reject reversed dates before running expense queries. Ensure the service and repository paths do not permit expenses belonging to another user to leak into results.
- Reuse existing CSS variables and profile naming conventions. Keep the controls keyboard-accessible and usable at the existing mobile breakpoints.
- Do not add a database, ORM, migration framework, JavaScript framework, or unrelated profile functionality.

## Definition of done

- [ ] An authenticated request to `/profile` with no date parameters defaults to the current UTC calendar month and preserves the existing default summary behavior.
- [ ] The profile provides clickable “This month,” “Last 3 months,” and “Last 6 months” links that submit the proper date range through query parameters.
- [ ] The “Last 3 months” preset includes the current UTC month and the previous two complete UTC calendar months; “Last 6 months” includes the current UTC month and the previous five complete UTC calendar months.
- [ ] The active preset is identified visually and accessibly.
- [ ] The profile renders custom date inputs containing the effective start and end dates, and submitting the form filters the page using the same query parameters as the presets.
- [ ] A valid custom inclusive date range filters the summary total, count, top category, category breakdown, and transaction list consistently.
- [ ] The inclusive end date includes expenses throughout that UTC date by using the correct half-open timestamp bound.
- [ ] If only one date is supplied, the missing bound defaults to the corresponding current-month boundary.
- [ ] A reversed date range returns a clear `400` response without querying expense data; malformed date values return `422`.
- [ ] The transaction table displays every row in the selected range, with deterministic newest-first ordering for matching timestamps.
- [ ] The transaction section identifies the active date range and makes clear it displays all matching transactions.
- [ ] Aggregate values use every matching transaction and are always scoped to the authenticated user.
- [ ] An empty selected range renders valid zero and empty values without division errors or sample-data fallbacks.
- [ ] Anonymous and stale-session behavior, route naming, and generic logged database failures remain unchanged.
- [ ] Tests cover current UTC-month defaults, preset date calculations (including year boundaries), custom and inclusive boundaries, partial bounds, reversed/malformed ranges, user scoping, empty results, and retrieval without an arbitrary row limit.
- [ ] Presets and custom filter controls follow existing Finzo styles and remain keyboard-accessible and usable at existing responsive breakpoints.
- [ ] The application retains its existing UTC service calculations and UTC MySQL session; no new timezone configuration is introduced.
- [ ] No schema changes, new dependencies, SQLAlchemy, Alembic, or additional routes are introduced.
