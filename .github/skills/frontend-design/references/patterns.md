# Reusable patterns

## Service shape (route stays thin)

Route:
1. `user_id = get_session_user_id(request)`; if `None`, redirect to `/login` (303).
2. `context = get_<page>_context(user_id)`; if `None`, clear the session and redirect.
3. Render the template with `context`.

Service (`services/<page>_service.py`):
- Real data from repositories where they exist (for example `get_user_by_id`, which must not select `password_hash`).
- `_sample_*()` functions for data that has no repository yet, returning raw values (`date`, `Decimal`, category text), not display strings.
- `_build_*()` functions that turn raw values into display-ready dicts via formatting helpers.
- The context includes `summary.is_sample`; the template shows its "sample data" notice only when it is true.
- Empty and zero cases are safe: no division by zero, empty lists render empty states.

Replacing sample data later means swapping the `_sample_*` bodies for repository calls with the same return shapes.

## Formatting helpers
- Currency: `₹` plus Indian grouping (`1,23,456`); drop `.00`; keep paise when non-zero; negative as `-₹1,500`.
- Dates: `f"{d.day:02d} {d:%b} {d.year}"` gives `02 Oct 2026`; member since gives `September 2026`.
- Initials: first letter of first and last word; one word gives two letters; blank name falls back to the email.
- Category class: lowercase, non-alphanumerics to `-`, prefixed `category-` (empty gives `category-general`).
- Percent shares: round half up; the sample data should sum to 100.

## Category color system (CSS)
Each category class only sets one custom property; badges and progress bars derive everything else from it, so adding a category is one rule.

```css
.profile-category-badge {
    --category-color: var(--ink-muted);                 /* neutral fallback for unknown categories */
    background: var(--paper-warm);                      /* fallback for browsers without color-mix */
    background: color-mix(in srgb, var(--category-color) 12%, var(--paper-card));
    color: var(--ink-soft);
    color: color-mix(in srgb, var(--category-color) 75%, var(--ink));
}
.profile-category-badge.category-food,
.profile-progress.category-food { --category-color: var(--accent); }
```

Mapping used so far: Food `--accent`, Travel `--accent-2`, Bills `--ink-muted`, Entertainment `--accent-4`, Education `--accent-3`, Health `--danger`. The 75% mix with `--ink` keeps badge text at 4.5:1 or better.

## Validation harness (when FastAPI/PyMySQL are unavailable)
- Stub `database/__init__.py` with a recording `execute_query`.
- Copy the user's real `base.html` into the sandbox.
- Fake request object with `session` dict and `url_for(name, **kw)`.
- Jinja2 `Environment(loader=FileSystemLoader("templates"), autoescape=select_autoescape())`.
- Run in `bash -c` when you need brace expansion (`sh` is dash here).