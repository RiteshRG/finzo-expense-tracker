# Spec: Analytics Module

## Overview

Add an authenticated Analytics destination to the main navigation and an initial server-rendered Coming Soon page. Match the attached Advanced Analytics reference: a quiet neutral page background, a centered white card with a soft shadow and rounded corners, a dark-green clock tile, a Coming Soon pill, a serif “Advanced Analytics” heading, explanatory copy, decorative progress dots, and a short closing message.

Use Finzo branding and the existing shared layout and design tokens. Do not copy or replace the navbar from the reference image. This is a presentation-only placeholder; it does not display charts, reports, spending analysis, or sample analytics data.

## Depends on

- Step 3: Login and Logout — signed sessions identify authenticated users.
- Existing FastAPI app, `dependencies/auth.py`, shared `templates/base.html`, and `static/css/style.css`.

## Routes

- `GET /analytics` — render the authenticated user's Analytics Coming Soon page.
  - Keep the route name `analytics` for template links using `request.url_for('analytics')`.
  - Reuse `get_session_user_id(request)` from `dependencies/auth.py`.
  - If the session has no valid positive integer user ID, clear a malformed `user_id` session value when present and redirect to `/login` with status `303`.
  - On success, render `templates/analytics.html` using the shared base template.
  - Do not query MySQL or require user/expense records; this placeholder only needs the existing authenticated session.

## Database changes

None. Do not add database queries, schema changes, analytics services, or repositories for this placeholder page.

## Templates

### Create

- `templates/analytics.html`
  - Extend `base.html`; do not duplicate the shared navigation or footer.
  - Present the reference's Coming Soon / Advanced Analytics card with the clock icon, status pill, heading, explanatory copy, three decorative dots, and closing message.
  - Keep visible status text so the coming-soon state is not conveyed by color or decorative graphics alone. Mark decorative icons and dots as hidden from assistive technology.
  - Use semantic heading order, and retain a clear focus treatment if any interactive element is added.
  - Do not add links, forms, charts, reports, or invented spending values.

### Modify

- `templates/base.html`
  - Add an Analytics link in the existing authenticated navigation only; logged-out navigation must continue to show only its current sign-in and registration options.
  - Link to `request.url_for('analytics')`.
  - Mark the Analytics link as the current page when viewing Analytics, using an accessible current-page indication as well as a visual active state.
  - Preserve the existing Profile and sign-out navigation and all logged-out navigation behavior.

## Files to change

- `app.py` — include the Analytics router without changing existing routes.
- `templates/base.html` — add the authenticated Analytics navigation link and active state hook.
- `static/css/style.css` — style the Analytics navigation active state and the new page with existing CSS tokens and responsive breakpoints.
- `tests/test_07-analytics-module.py` — cover page access, navigation visibility and active state, and Coming Soon rendering.

## Files to create

- `routes/analytics.py` — thin authenticated page route.
- `templates/analytics.html` — Coming Soon page extending `base.html`.

## New dependencies

None.

## Rules for implementation

- Follow the existing FastAPI, Jinja2, session-authentication, and shared-template patterns.
- Use the existing `get_session_user_id(request)` helper; do not introduce a second authentication mechanism or a new auth dependency.
- Keep the route thin and do not add database, service, or repository work for a static placeholder.
- Use existing Finzo CSS variables, typography, naming conventions, and responsive breakpoints. Do not introduce inline styles, a separate stylesheet, new frameworks, or dependencies.
- Keep Analytics out of navigation for logged-out or invalid-session users. Clear malformed stored session data and redirect invalid sessions to `/login` with status `303`.
- Preserve existing routes, Profile navigation, sign-out behavior, and logged-out navigation.
- Do not add actual analytics functionality, charts, reports, sample metrics, expense calculations, or unrelated features.

## Definition of done

- [ ] An authenticated user sees an Analytics option in the main navigation.
- [ ] A logged-out visitor does not see the Analytics navigation option.
- [ ] Clicking the Analytics navigation option opens `GET /analytics`.
- [ ] The Analytics navigation item has a visible active state and an accessible current-page indication on the Analytics page.
- [ ] An authenticated request to `GET /analytics` returns `200` and renders the Advanced Analytics Coming Soon design described above.
- [ ] A logged-out direct request to `/analytics` redirects to `/login` with status `303`.
- [ ] Missing or malformed session user IDs are rejected, and malformed stored session data is cleared.
- [ ] The page extends the shared base template and remains usable at the existing responsive breakpoints.
- [ ] No database queries, schema changes, actual analytics, new dependencies, or changes to existing authentication behavior are introduced.
- [ ] Tests cover anonymous and authenticated page access, navigation visibility and active state, and the key Coming Soon content.
