# Finzo architecture snapshot (as of Oct 2026)

Verify every item against the files the user provides. This is a map, not a source of truth.

## Layout
- `app.py` is the FastAPI entry point (there is no `main.py`). It sets up `SessionMiddleware`, mounts `/static`, creates `Jinja2Templates(directory="templates")`, and defines `/`, `/terms`, `/privacy`, `/profile` and placeholder expense routes directly. It includes `routes/auth.py` for register, login, logout.
- `routes/expenses.py` is empty and not included.
- `dependencies/auth.py`: `get_session_user_id(request)` returns the int user id or `None`; `get_current_user_id(request)` raises HTTP 401. Pages redirect to `/login` with status 303 when the id is `None`.
- `database/__init__.py`: PyMySQL layer. `execute_query(query, params=None, fetch=False)` returns rows (dicts via `DictCursor`) when `fetch=True`, else the last row id. Needs `DATABASE_URL` (`mysql+pymysql://user:pass@host:3306/db`). `database.py` at the root is a compatibility wrapper.
- `repositories/user_repository.py`: `get_user_by_email`, `create_user`, and (after the profile work) `get_user_by_id`.
- `services/auth_service.py` verifies Werkzeug password hashes. There were no expense services or repositories.
- Startup runs `init_db()` and `seed_db()` and swallows exceptions, so a bad database config can be invisible until a page queries it.
- Sessions: Starlette signed cookie holding `user_id`; no JWT.

## Templates
- `templates/base.html`: navbar (profile link and POST sign-out when `request.session.get('user_id')`, otherwise sign-in/register), `{% block title %}`, `{% block head %}`, `{% block content %}`, `{% block scripts %}`, footer, `static/js/main.js` (an empty placeholder).
- Links use `request.url_for('route_name')`, so keep route names stable.
- `landing.html` has inline JS for a modal and illustrative figures. No dashboard or expenses template existed.

## CSS
- `static/css/style.css`: shared. `:root` tokens: `--ink`, `--ink-soft`, `--ink-muted`, `--ink-faint`, `--paper`, `--paper-warm`, `--paper-card`, `--accent`, `--accent-light`, `--accent-2`, `--accent-2-light`, `--danger`, `--danger-light`, `--border`, `--border-soft`, `--font-display` (DM Serif Display), `--font-body` (DM Sans), `--max-width: 1200px`, `--auth-width`, `--radius-sm/md/lg` (6/12/20px). The page sections come in a banner-comment order; the profile section is last.
- `landing.css`: landing page only.
- Breakpoints: 900px and 600px in `style.css` (landing also uses 620px and 360px).
- The stylesheet hardcodes `#5b7fa6` and `#8b5e83` in landing mock bars; these became `--accent-3` and `--accent-4`.

## Schema
- `users(id, name, email UNIQUE, password_hash, created_at, updated_at)`; `name` may be an empty string for legacy rows.
- `expenses(id, user_id FK, title, amount DECIMAL(10,2), category VARCHAR(100) default 'general', description, created_at, updated_at)`.
- No categories table. Seeded categories: Food, Travel, Bills, Entertainment, Health, Education.

## Conventions
- Currency symbol ₹; dates `DD Mon YYYY`; "Member since" as `Month YYYY`.