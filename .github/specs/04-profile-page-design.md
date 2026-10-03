# Spec: Profile Page

## Overview
This feature replaces the existing `/profile` stub with a fully designed Finzo profile page using static, hardcoded data.

The goal is to establish the complete profile UI layout — user information card, expense summary statistics, recent transaction history, and category breakdown — before connecting the page to real MySQL queries.

Building the UI first allows the design and template structure to be validated independently from the database layer. The real user and expense data will be connected in a later step.

## Depends on
- Step 1: Database setup (MySQL schema must exist)
- Step 2: Registration (user accounts must be creatable)
- Step 3: Login + Logout (authentication/session must be available; `/profile` must be protected)

## Routes
- GET /profile — render the profile page — logged-in users only
  - If the user is not authenticated, redirect to `/login`
  - If authenticated, render `templates/profile.html`
  - No MySQL queries are required in this step

## Database changes
No database changes.

The existing `users` and `expenses` tables are sufficient for the profile page.

The page will use hardcoded data in this step. Real database queries will be introduced in a later step.

## Templates
- Create: `templates/profile.html`

The template must extend the existing `base.html` and contain four main sections:

### 1. User Information Card
Display:
- Avatar initials
- User name
- Email
- Member-since date

For this step, these values should be provided as hardcoded context data from the route.

### 2. Summary Statistics
Display at least three summary values, such as:
- Total spent
- Number of transactions
- Top spending category

The values should be hardcoded for this step.

### 3. Recent Transaction History
Display a transaction table containing hardcoded expense records.

Each row should contain:
- Date
- Description
- Category
- Amount

Use at least three example transactions.

Category values should be displayed using the existing Finzo category badge styling.

### 4. Category Breakdown
Display spending by category using hardcoded data.

The section can use:
- Simple category rows
- Progress bars
- Category totals

At least three categories should be displayed.

The UI should be structured so that the hardcoded data can later be replaced with real database data without requiring a major template redesign.

## Files to change

### Route
Modify the existing profile route in the appropriate FastAPI route module, for example:

`routes/profile.py`

or the existing module where the `/profile` route is currently defined.

The route should:

- Check whether the user is authenticated using the existing Finzo authentication dependency/mechanism
- Redirect unauthenticated users to `/login`
- Pass hardcoded profile data to the Jinja2 template
- Render `templates/profile.html`
- Not perform MySQL queries in this step

Do not create a duplicate `/profile` route if one already exists.

### Existing shared files
Modify existing shared files only if required for the profile page.

For example:
- `templates/base.html`
- `static/css/style.css`
- `static/js/app.js`

Preserve existing Finzo functionality and styling.

## Files to create
- `templates/profile.html`

Only create additional files if the existing project structure requires them.

## New dependencies
No new dependencies.

Use the dependencies already present in the Finzo project.

## Rules for implementation

### Backend
- Use FastAPI.
- Use Jinja2 templates.
- Use the existing Finzo route/service/repository/dependency structure.
- Do not introduce SQLAlchemy.
- Do not introduce Alembic.
- Do not introduce another ORM.
- Do not add database queries in this step.
- Do not duplicate authentication logic if an existing authentication dependency already exists.
- Use the existing login/session mechanism for determining whether the user is authenticated.
- Do not hardcode passwords, database credentials, or secrets.

### Database
- The project uses MySQL with PyMySQL.
- No database changes are required for this step.
- Do not add MySQL queries merely to populate the profile page.
- Real database integration will be handled in a later step.

### Templates
- `profile.html` must extend `base.html`.
- Reuse the existing Finzo layout and navigation.
- Do not duplicate the navbar or common page layout.
- Use Jinja2 variables for all profile data.
- Keep the template structured so hardcoded data can later be replaced by database data.
- Do not put business logic in the template.

### Styling
- Reuse the existing Finzo CSS architecture.
- Use CSS variables for colors and shared design values.
- Do not hardcode hex color values in `profile.html`.
- Do not use inline styles.
- Category badges must use CSS classes.
- Follow the existing Finzo visual style rather than introducing an unrelated design.
- Keep the page responsive.

### Data
All profile information for this step must be provided as hardcoded Python dictionaries/lists from the route or appropriate service layer.

Example categories of context:

- `user`
- `summary`
- `transactions`
- `category_breakdown`

Do not query MySQL for these values in this step.

## Definition of done

- [ ] Visiting `/profile` without being authenticated redirects to `/login`
- [ ] Visiting `/profile` while authenticated returns HTTP 200
- [ ] `profile.html` extends `base.html`
- [ ] The page displays a user information card
- [ ] The user information card displays a name and email
- [ ] The page displays a member-since date
- [ ] The page displays at least three summary statistics
- [ ] The page displays a recent transaction history table
- [ ] The transaction table contains at least three hardcoded transactions
- [ ] Each transaction displays date, description, category, and amount
- [ ] Category badges use CSS classes
- [ ] The page displays a category breakdown
- [ ] The category breakdown contains at least three categories
- [ ] The navbar continues to display the correct logged-in state using the existing Finzo authentication system
- [ ] No MySQL queries are required to render the profile page in this step
- [ ] No SQLAlchemy or Alembic is introduced
- [ ] No new dependencies are introduced
- [ ] No inline styles are used
- [ ] No hardcoded hex color values appear in `profile.html`
- [ ] Existing Finzo routes and functionality continue to work
- [ ] The page follows the existing Finzo visual style