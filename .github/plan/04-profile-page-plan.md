# Profile Page Implementation Plan

## TL;DR

Replace the `/profile` placeholder with an authenticated, responsive Finzo profile page. Render the profile card, summary statistics, recent transaction table, and category breakdown from hardcoded Python context data, as required by Step 04. Do not query MySQL or add database, expense, or profile-editing behavior.

Keep the implementation focused on the current app structure: update the existing `/profile` route in `app.py`, add `templates/profile.html`, add profile-specific styles to `static/css/style.css`, and show a profile link in the authenticated navigation in `templates/base.html`. Reuse the existing session authentication validation in `dependencies/auth.py` without changing the 401 behavior expected by the logout route.

---

## Findings from the Repo

- `.github/specs/04-profile-page-design.md` is the source of truth for this step. It specifies hardcoded profile and expense example data, four UI sections, authenticated-only access, and no database queries.
- `app.py` currently owns the landing, terms, and privacy page routes. Its `/profile` route is a placeholder returning plain text; no duplicate profile route exists.
- `dependencies/auth.py` provides `get_current_user_id`, which validates the session `user_id` and raises HTTP 401 when it is missing or malformed. `routes/auth.py` uses this dependency for logout, where the 401 behavior must remain intact.
- `templates/base.html` already switches navigation based on `request.session['user_id']`. Authenticated navigation currently only has the POST sign-out form; anonymous navigation has sign-in and registration links.
- `templates/landing.html` demonstrates the existing Finzo visual conventions and expense summary presentation. `static/css/style.css` has shared colors, typography, cards, buttons, and responsive styles but no profile page or category-badge component.
- The existing project uses FastAPI, Jinja2, session middleware, and pytest. No additional package or database work is needed.

---

## 1. Confirm the page contract and mock-data boundary

Keep route and template data explicit and presentation-oriented. Pass separate structures to Jinja rather than embedding values or business calculations in the template:

- `user`: display name, email, avatar initials, and a formatted member-since date
- `summary`: at least three labeled metrics, including a currency-formatted total, a transaction count, and a top category
- `transactions`: at least three recent records, each with a display date, description, category label/class, and amount
- `category_breakdown`: at least three categories with labels, category classes, and amounts; optionally include progress values if they can be rendered without inline styles

Use a clearly identified example/demo dataset so authenticated users are not misled into thinking these hardcoded transactions are their real account activity. Keep the context shape stable and simple to replace with real database results in a later step.

Keep the example internally understandable: label the period represented by summary metrics, and align breakdown totals with that period when the chosen values make that feasible. Do not calculate actual expense analytics from nonexistent database data.

---

## 2. Protect `/profile` using the existing session mechanism

Update the existing route in `app.py`; do not add a second `/profile` route or create a new route module for this single page.

- Add `Request` to the route signature so the route can render a Jinja response and inspect the current session through the existing auth mechanism.
- Reuse the session-ID validation logic from `dependencies/auth.py` to determine whether the session has a valid positive integer user ID.
- Preserve `get_current_user_id`'s existing HTTP 401 contract so logout and any API-style callers are not changed.
- If the session is absent or malformed, return a `RedirectResponse` to `/login` with HTTP 303 as required by the spec.
- If authenticated, render `profile.html` with the hardcoded context structures above.
- Keep the route read-only: do not call a repository, service, `execute_query`, or any MySQL function.
- Keep the mock profile values independent of identity supplied through query parameters or form fields. Do not accept a user ID from the request URL.

If reusing the current dependency requires an adjustment, extract a small shared session-ID parsing helper in `dependencies/auth.py`, then have both the existing 401 dependency and the profile route use that helper. Do not weaken the logout dependency or duplicate its validation rules.

---

## 3. Build the Jinja profile page

Create `templates/profile.html` extending `base.html`. Keep the shared navbar, footer, and common scripts in the base template; do not duplicate them.

Add four clear page sections:

1. **Profile header/card**
   - Show initials in an avatar element, user name, email, and member-since date.
   - Use semantic headings and ensure the avatar does not replace the accessible name text.
   - Indicate that this page currently contains sample/demo activity.

2. **Summary statistics**
   - Render at least three metrics from `summary`.
   - Include visible labels and accessible text; do not rely on icons or color alone.
   - Format currency consistently with the rest of Finzo's rupee-oriented UI.

3. **Recent transactions**
   - Render a semantic table with a caption or heading and column headers for date, description, category, and amount.
   - Iterate over the transaction context; do not hardcode rows in the template.
   - Format amounts consistently and render category badges using CSS classes supplied through the known mock dataset.
   - Ensure the table remains usable on narrow screens, using a horizontal overflow wrapper or an equivalent responsive layout.

4. **Category breakdown**
   - Render at least three categories from `category_breakdown`.
   - Show category labels and totals. If progress indicators are used, provide accessible text/value semantics and avoid inline styles; use the HTML `<progress>` element or another class-based implementation.
   - Apply the same category class system used in the transaction table.

Keep template logic to iteration and display formatting only. Do not add database access, calculations, or inline CSS.

---

## 4. Add profile-specific responsive styling

Append a clearly grouped profile section to `static/css/style.css`, reusing the existing design tokens and conventions:

- Use `--paper`, `--paper-card`, `--ink`, `--ink-muted`, `--accent`, `--accent-light`, `--accent-2`, `--border`, and existing radius/font variables rather than hardcoded colors.
- Use responsive CSS grid/flex layouts for the profile header and summary cards, collapsing to one column on small screens.
- Style the profile card, section headings, statistics, transaction table, category rows, avatar, demo-data note, and category badges.
- Define reusable category badge classes and a small set of category variants used by the sample data. Do not build selectors from arbitrary user-provided strings.
- Maintain visible focus states and sufficient contrast consistent with the current site.
- Do not add inline styles or JavaScript for layout, charting, or sample data.

Review existing media queries near the bottom of the stylesheet before adding breakpoints; extend existing responsive patterns instead of duplicating or conflicting with them.

---

## 5. Add an authenticated profile navigation link

Modify the authenticated branch in `templates/base.html` to include a link to the named profile route alongside the existing POST sign-out form.

- Keep the existing session-based authenticated/anonymous conditional.
- Preserve the POST method and action for logout.
- Leave the anonymous sign-in and get-started links unchanged.
- Use `request.url_for('profile')` (or the actual named route URL helper) instead of hardcoding a second route definition.
- Keep the link visible and keyboard-accessible at desktop and mobile widths.

---

## 6. Add focused route and rendering tests

Create `tests/test_profile.py` following the existing `TestClient` and `monkeypatch` patterns. Avoid depending on a live MySQL instance.

Cover:

1. Anonymous `GET /profile` returns HTTP 303 and points to `/login`.
2. Authenticated `GET /profile` returns HTTP 200 and renders the profile page.
3. The page includes name, email, initials, member-since date, and at least three summary values.
4. The transaction table renders at least three rows with date, description, category, and amount.
5. The category breakdown renders at least three entries and badges have CSS-backed class names.
6. Authenticated navigation includes the profile link and POST sign-out control; anonymous navigation remains unchanged.
7. Malformed or non-positive session IDs are treated as unauthenticated and redirected, without exposing the profile.
8. The profile route does not invoke database access. Stub database access to fail if called during a profile request, while accounting for existing app startup behavior in the test setup.
9. The template extends the base layout and contains no inline style attributes or hardcoded hex color values.

For authenticated requests, establish the session through the existing login flow with `authenticate_user` monkeypatched as in `tests/test_auth_login.py`, or use the repository's established session-test pattern if one is added before implementation. Do not forge or hardcode a session signing key in production code.

---

## 7. Validate the change

Run the focused tests first:

```text
pytest tests/test_profile.py tests/test_auth_login.py
```

Then run the full existing test suite if the focused tests pass:

```text
pytest
```

Review the final diff to confirm:

- Only the profile route, authentication helper if needed, shared navbar, shared stylesheet, new profile template, and focused tests changed.
- No SQL, database repository calls, migrations, new dependencies, expense CRUD, profile editing, or unrelated routes were added.
- All links resolve and the unauthenticated route response is a 303 to `/login`.
- CSS remains responsive, and the profile page has no inline styles or hex color values in its template.

---

## Scope Boundaries

In scope:

- Protected, read-only `/profile` page
- Static Python mock data for profile details, summary metrics, transactions, and category breakdown
- Responsive Jinja2 UI consistent with Finzo's shared design
- Authenticated navbar profile link
- Focused tests for route protection and rendered UI

Out of scope:

- Any MySQL reads or writes
- Real user or expense data integration
- Profile editing or account settings
- Expense creation, editing, deletion, or filtering
- New authentication/session features
- New libraries, ORM, or migration framework
- Changes to anonymous navigation, login, registration, or logout behavior
