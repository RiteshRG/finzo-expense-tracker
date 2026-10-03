---
description: Runs parallel security and quality code review for a specific Finzo feature. Pass the spec name as argument e.g. /code-review-feature 03-login-and-logout
allowed-tools: Bash(git diff), Bash(git status --short)
---

Run the full code review pipeline for the Finzo feature specified in $ARGUMENTS.

If no argument is provided, stop immediately and say:
"Please provide a spec name. Usage: /code-review-feature
<spec-name> e.g. /code-review-feature 03-login-and-logout"

## Pre-flight Check

Before invoking any subagents, collect the diff:

- Run `git diff HEAD` to capture staged and unstaged tracked changes together.
- Run `git status --short` to identify newly added, untracked project files; ordinary diffs do not include their contents.
- Include relevant untracked source and test files in the review by providing their paths and having the reviewers inspect them directly.
- Exclude ignored/generated files, virtual environments, caches, and `.env` files. Never read or disclose `.env` values.

If there are no tracked changes and no relevant untracked project files, stop immediately and say:
"No changes detected. Implement the feature before running code review."

---

## Spec Check

Before invoking any subagents, verify that:

`.github/specs/$ARGUMENTS.md`

exists.

If the spec file does not exist, stop immediately and say:

"Spec file not found at .github/specs/$ARGUMENTS.md.
Please check the spec name and try again."

Do not proceed without the specification.

---

## Step 1: Parallel Review

Invoke both subagents simultaneously with the same context.

### finzo-security-reviewer

Provide:

- The combined diff from the pre-flight check
- Paths of relevant untracked source and test files, if any
- Spec file:
  `.github/specs/$ARGUMENTS.md`
- Relevant changed files and supporting project context, as needed:
  - `.github/copilot-instructions.md`
  - FastAPI application entry point (currently `app.py`)
  - `routes/`, `services/`, `repositories/`, and `dependencies/`
  - `database.py` and/or `database/` (use the helper the changed code actually imports)
  - `models.py`, `schemas.py`, and relevant files under `database/`
  - `templates/`, `static/`, and relevant tests under `tests/`

Inspect only changed files and the nearby context needed to assess them. Do not read `.env` files.

Instruction:

> Review only the changed code for security concerns. Focus on SQL injection, authentication, authorization, sensitive data exposure, XSS, CSRF awareness, input validation, secrets, and other relevant application-security issues. Do not review code quality, naming, architecture, or style.

### finzo-quality-reviewer

Provide:

- The combined diff from the pre-flight check
- Paths of relevant untracked source and test files, if any
- Spec file:
  `.github/specs/$ARGUMENTS.md`
- Relevant changed files and supporting project context, as needed:
  - `.github/copilot-instructions.md`
  - FastAPI application entry point (currently `app.py`)
  - `routes/`, `services/`, `repositories/`, and `dependencies/`
  - `database.py` and/or `database/` (use the helper the changed code actually imports)
  - `models.py`, `schemas.py`, and relevant files under `database/`
  - `templates/`, `static/`, and relevant tests under `tests/`

Inspect only changed files and the nearby context needed to assess them. Do not read `.env` files.

Instruction:

> Review only the changed code for code quality, maintainability, FastAPI/Jinja2 practices, project organization, readability, frontend organization, and consistency with the Finzo architecture. Do not comment on security concerns.

Both subagents must run in parallel.

Do not wait for one reviewer to finish before starting the other.

Pass the same change set and feature specification to both reviewers. Include new untracked files by path so the reviewers can read their contents; do not treat the absence of an untracked file from `git diff` as evidence that it has no changes.

---

## Step 2: Unified Report

Once both subagents have completed, combine their findings into one unified report.

De-duplicate overlapping findings. If both reviewers identify the same code location for different reasons, merge the findings while keeping both perspectives clear.

Structure the report as:

# Code Review Report — $ARGUMENTS

## Security Findings

[finzo-security-reviewer output]

## Quality Findings

[finzo-quality-reviewer output]

## Combined Action Plan

Create an ordered checklist of findings that need attention.

Use this order, without inventing severity labels that the reviews do not support:

1. Security findings with the greatest demonstrated impact (preserve any severity labels supplied by the reviewer)
2. Quality findings that require changes
3. Other security findings
4. Quality suggestions and optional improvements

For each action item include:

- File and line
- Finding
- Why it matters
- Recommended change

---

## Overall Review Status

Use one of:

### APPROVED — ready to commit

Use when no changes are required.

### APPROVED WITH SUGGESTIONS — can commit

Use when there are only optional improvements and no required fixes.

### CHANGES REQUESTED — fix before committing

Use when one or more important findings require changes.

---

## Step 3: Ask for Approval

After presenting the unified report, ask:

"Do you want me to implement the action plan now?"

Wait for explicit user confirmation before making any changes.

Do not modify files before approval.

---

## Rules

- Do NOT edit any files before user approval.
- Do NOT start one reviewer before the other; both must run in parallel.
- Do NOT skip the pre-flight diff check.
- Do NOT overlook relevant untracked source or test files; `git diff` does not include them.
- Do NOT proceed if `.github/specs/$ARGUMENTS.md` does not exist.
- Do NOT use the old Spendly/Flask/SQLite architecture.
- Finzo uses FastAPI, MySQL, PyMySQL, Jinja2, HTML, CSS, and vanilla JavaScript.
- Do NOT introduce SQLAlchemy, Alembic, SQLite, React, or another ORM.
- Review only changed/new code unless additional source context is required to understand the change.
- If either subagent fails or returns no output, report the failure and do not present a partial review as complete.
- Do NOT automatically install packages.
- Do NOT modify production code, tests, configuration, or documentation before explicit user approval.
- Respect the feature specification and existing Finzo architecture.
- Keep security and quality responsibilities separate between the two reviewers.