---
name: finzo-page-builder
description: Build or improve a page in the Finzo expense-tracker app (FastAPI + Jinja2 + vanilla JS + MySQL via PyMySQL) so it matches the existing design system and architecture. Use whenever the user mentions Finzo, the expense tracker, or asks to create, redesign, or fix a page such as profile, dashboard, expenses, or transactions in a FastAPI/Jinja2 project. Also use for "match the existing design system", "reuse base.html and the CSS variables", "UI-first with mock data that MySQL can replace later", or "don't add React/SQLAlchemy". Use it even if the user does not name the page or the stack explicitly.
---

# Finzo page builder

Build or improve one page of Finzo so it looks and behaves like it was always part of the app. The risk with this kind of task is not writing code; it is writing code against a project you have not seen: duplicate CSS systems, a template that ignores `base.html`, database calls inside routes, a new dependency nobody asked for. So the job is mostly inspection and restraint.

## Stack and ground rules

FastAPI, Jinja2, HTML, CSS, vanilla JavaScript, MySQL through PyMySQL. Do not introduce React, Vue, SQLAlchemy, Alembic, any ORM, or a chart library unless the project already uses one. Keep database logic out of templates and out of route functions: routes call services, services call repositories, repositories call the PyMySQL helper.

`references/finzo-architecture.md` records what the repository looked like when this skill was written (file locations, auth helpers, CSS tokens, schema). Treat it as a hint about where to look, never as truth. Files move; verify against what the user gives you.

## Workflow

### 1. Get the real files before designing anything

You usually cannot reach the user's GitHub repo (fetching is blocked and the sandbox has no network). Do not guess the structure and do not write against the architecture description alone.

Ask once, specifically, for the contents of: the FastAPI entry point, the route file(s) for the page, the auth dependency, the repository for the data involved, the DB helper, `base.html`, the current template for the page (if any), the full stylesheet, and the schema. A zip without `venv/`, `.git/`, `__pycache__/` and `.env` is easiest. Windows `.url` shortcut files contain only a path on the user's PC, not code; if that is what arrives, say so and ask for pasted contents or the real files. Never ask for or read `.env` values.

Ask only the questions the files cannot answer: mock data or real MySQL, whether the page is display-only or editable, and whether they want whole files or patches. Accept sensible defaults if the user says "yes".

### 2. Inspect, then decide what already exists

Read the code in this order: entry point and the page's route, auth helpers, DB helper and repositories, `base.html`, a sibling page template, then the CSS (`:root` tokens first, then navbar, cards, tables, badges, media queries). Note the breakpoints and the naming prefix the page's existing CSS uses (for example `profile-*`).

Write down, for yourself, what is reusable and what is missing. If a template, class, or helper exists, extend it. A second stylesheet, a second badge system, or a parallel auth check is a defect even if it looks fine.

### 3. Design inside the system

- Extend `base.html` and fill its blocks; do not copy the navbar or footer.
- Use existing CSS variables for color, type, radius and spacing. If a color is missing, add a named token to `:root` (reusing a value the stylesheet already hardcodes elsewhere is a good source) rather than writing a hex value in a rule or a template.
- No inline `style=` attributes, no `<style>` blocks in templates, no `!important` (fix specificity instead).
- Follow the existing responsive breakpoints. Wide tables stay in a scroll wrapper that is keyboard focusable (`tabindex="0"`, `role="region"`, labelled). Long emails and names need `overflow-wrap`.
- Every list or table needs an empty state, because real data will eventually be empty for new users.
- Semantic HTML: headings in order, `scope` on table headers, `aria-label` on progress elements, decorative avatars `aria-hidden`.
- Colors must not be the only carrier of meaning (show the percentage as text beside a bar).

### 4. Data: UI-first without a redesign later

If the data layer for the page does not exist yet, create a small service module that returns the exact context the template needs. Real values (for example the logged-in user's name and email) come from the repository; the rest comes from `_sample_*` functions that can later be replaced by repository calls with the same shapes. Formatting (currency, dates, category CSS classes, percentages) lives in service helpers, not in the template and not in the route. Flag the sample data to the user in the UI only while it is sample, using a flag in the context so the notice disappears automatically once real data is wired in.

See `references/patterns.md` for the service shape, the category color system, and formatting conventions (₹ with Indian digit grouping, `DD Mon YYYY`).

### 5. Touch as little as possible

Change only files relevant to the page. Keep the existing route name (templates use `request.url_for('profile')` and similar), keep the auth behavior, and keep unrelated routes and placeholders as they are. Prefer patches or single replaced sections over rewriting shared files such as the stylesheet; when you do deliver whole files, say exactly which section of a shared file to replace and where it starts and ends.

Authentication for pages: use the project's existing session helper. A signed-out visitor is redirected to the login page; a session whose user no longer exists should clear the session and redirect too. Do not create a second way of checking login.

### 6. Validate honestly

Run whatever the environment allows and say which checks were real. If FastAPI or PyMySQL are not installed (common in the sandbox), do not claim the route was tested. Instead:

- compile every Python file and confirm imports line up
- test service logic against a stubbed `database` module (parameterised SQL, missing user, blank name, zero counts, rounding that sums to 100)
- render the template with Jinja2 against the user's real `base.html` using a fake request, for the normal case, empty lists, unknown category, missing optional fields, and an HTML-injection name
- check the CSS: balanced braces, no hex/rgb outside `:root`, no `!important`, every `var(--x)` defined, every static template class has a rule, badge text contrast of at least 4.5:1
- warn the user about what you could not verify: the live route, the live database, a browser view at roughly 1200, 800 and 375px, and existing tests that may now need a patched repository

### 7. Report

End with a short report covering: files inspected, files created or modified (with where each goes), what was implemented, what was validated and how, and what the user must check themselves. Mention any behavior change, for example "this page now needs MySQL to be reachable". Keep the tone plain; no postamble.

## Common mistakes

- Designing before seeing the CSS, then inventing a new look.
- Putting SQL in `app.py` or formatting logic in Jinja.
- Hardcoding category colors per template instead of per CSS class.
- Treating a category as a fixed enum; it is free text in the database, so unknown values need a neutral fallback class.
- Saying "tested" when only a stub was exercised.