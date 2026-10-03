---
description: Writes and runs tests for a specific Finzo feature. Pass the spec name as argument e.g. /test-feature 05-backend-connection
allowed-tools: Bash(python -m pytest)
---

Run the full testing pipeline for the Finzo feature specified in
$ARGUMENTS.

If no argument is provided, stop immediately and say:

"Please provide a spec name. Usage: /test-feature
<spec-name> e.g. /test-feature 05-backend-connection"

If `.github/specs/$ARGUMENTS.md` does not exist, stop
immediately and say:

"Spec file not found at .github/specs/$ARGUMENTS.md.
Please check the spec name and try again."

---

## Step 1: Write Tests

Invoke the **finzo-test-writer** subagent with the
following context:

- Spec file to base tests on:
  `.github/specs/$ARGUMENTS.md`

- Source files/directories to inspect for project structure:
  - `app.py` or the actual FastAPI application entry point
  - `database/` directory, if present
  - `routes/` directory, if present
  - `services/` directory, if present
  - `repositories/` directory, if present
  - `dependencies/` directory, if present
  - `templates/` directory, if relevant
  - `static/` directory, if relevant
  - `tests/` directory

- Output test file to create:
  `tests/test_$ARGUMENTS.py`

- Instruction:
  Write tests based on what the specification says the feature
  SHOULD do.

  Do NOT derive the expected behavior from reading the implementation.

  Cover relevant:
  - happy paths
  - edge cases
  - authentication guards
  - authorization/ownership
  - validation errors
  - HTTP status codes
  - database side effects
  - template rendering where applicable

  Follow the existing Finzo testing structure.

  Finzo uses:
  - FastAPI
  - MySQL
  - PyMySQL
  - Jinja2
  - pytest

  Do NOT introduce:
  - Flask
  - SQLite
  - SQLAlchemy
  - Alembic
  - any ORM
  - React
  - another database driver

Wait for **finzo-test-writer** to fully complete and confirm that
the test file has been written before proceeding to Step 2.

---

## Step 2: Run Tests

Once **finzo-test-writer** has finished, invoke the
**finzo-test-runner** subagent with the following context:

- Test file to execute:
  `tests/test_$ARGUMENTS.py`

- Spec file for context:
  `.github/specs/$ARGUMENTS.md`

- Source files/directories to analyze when diagnosing failures:
  - FastAPI application entry point
  - `database/`
  - `routes/`
  - `services/`
  - `repositories/`
  - `dependencies/`
  - relevant `templates/`
  - relevant `static/`

- Run command:
  `python -m pytest tests/test_$ARGUMENTS.py -v`

- Instruction:
  Run ONLY the specified test file.

  Do NOT run the full test suite.

  Analyze failures by cross-referencing:
  1. the test code
  2. the feature specification
  3. the relevant source files

  Classify each failure as:
  - application bug
  - missing/incomplete feature
  - incorrect test assumption
  - test/environment configuration problem
  - database/test environment problem

  Do NOT modify production code or tests to make the
  tests pass.

---

## Handoff Rules

- Do NOT start Step 2 until Step 1 is fully complete.
- Do NOT attempt to fix any code regardless of test results.
- Do NOT run tests beyond `tests/test_$ARGUMENTS.py`.
- If `finzo-test-writer` reports that it could not write the test
  file, stop and report the reason.
- Do NOT proceed to Step 2 if the test file does not exist.
- Do NOT install packages automatically.
- Never use the production database for tests.
- Never switch to SQLite as a testing workaround.

---

## Final Output

After both subagents complete, produce a combined summary:

### Testing Pipeline Report — $ARGUMENTS

**Step 1 — Tests Written**

- List each test written with a one-line description of the
  specification requirement it validates.

**Step 2 — Test Results**

Mirror the structured report produced by
**finzo-test-runner**, including:

- Test file
- Command executed
- Total tests
- Passed
- Failed
- Errors
- Skipped
- Pass rate
- Failures and root causes
- Warnings/architecture flags
- Environment/database issues

### Verdict

Use one of:

- ✅ **Ready for code review — all tests pass**
- ❌ **Needs fixes — list the failing tests and their root causes**
- ⚠️ **Blocked — test environment/configuration must be fixed before results are meaningful**