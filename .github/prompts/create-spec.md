---
description: Create a spec file and feature branch for the next Finzo step
argument-hint: "Step number and feature name e.g. 2 registration"
---

You are a senior developer working on the Finzo expense tracker.

Always follow `.github/copilot-instructions.md`.

User input:
$ARGUMENTS

## 1. Check Git

- Check `git status`.
- If there are uncommitted changes, stop and ask the user to clean the working tree.

## 2. Parse input

From the user's input, determine:

- Step number
- Feature title
- Feature slug
- Branch name

Example:

`2 registration`

becomes:

```text
step: 02
title: Registration
slug: registration
branch: feature/02-registration
```

## 3. Create branch

- Check that the branch does not already exist.
- Switch to `main`.
- Pull the latest changes.
- Create and switch to:

```text
feature/<step>-<feature-slug>
```

## 4. Research the project

Inspect the existing project before creating the spec.

Check relevant files such as:

```text
.github/copilot-instructions.md
app.py
database/
routes/
services/
repositories/
dependencies/
templates/
static/
requirements.txt
.env.example
.github/specs/
.github/plans/
```

Do not assume files exist.

Check whether the feature is already implemented or partially implemented.

## 5. Create the spec

Create:

```text
.github/specs/<step>-<feature-slug>.md
```

Use this structure:

```markdown
# Spec: <feature_title>

## Overview

## Depends on

## Routes

## Database changes

## Templates

### Create

### Modify

## Files to change

## Files to create

## New dependencies

## Rules for implementation

## Definition of done
```

Follow the existing Finzo architecture.

Project rules:

- FastAPI
- MySQL
- PyMySQL
- Jinja2 + HTML/CSS/JavaScript
- No SQLAlchemy
- No Alembic
- Use parameterized SQL
- Keep secrets in environment variables
- Use existing routes/services/repositories structure
- Do not duplicate existing logic
- Preserve existing functionality
- Do not add unrelated features

## 6. Final response

Do not print the full spec.

Report:

```text
Branch:    <branch_name>
Spec file: .github/specs/<step>-<feature-slug>.md
Title:     <feature_title>
```

Then say:

`Review the spec, then enter Plan mode to begin implementation.`
