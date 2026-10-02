# Finzo — Database Setup Specification

## 1. Project Overview

Finzo is a personal expense tracking web application.

The application allows users to:

- Create an account
- Log in
- Track personal expenses
- Organize expenses by category
- View their expense data

This specification covers only the initial database setup.

The current task is to create and configure the MySQL database, database schema, direct Python database connection, initialization, and demo seed data.

Do not implement authentication, dashboards, expense APIs, or other application features in this task.

---

## 2. Scope

This task includes:

- MySQL database configuration
- MySQL connection from FastAPI
- Direct Python database access through PyMySQL
- Explicit SQL query handling in Python
- Database initialization
- Users table
- Expenses table
- Primary keys
- Foreign keys
- Unique email constraint
- Demo seed data
- Safe repeated initialization
- Safe repeated seeding
- Database error handling
- Basic database validation

This task does NOT include:

- Login functionality
- Registration API
- Password authentication logic
- Expense CRUD API
- Dashboard
- Budget functionality
- AI features
- Analytics
- Frontend changes
- Deployment configuration

---

# 3. Technology Stack

Use the following technologies:

- Python
- FastAPI
- MySQL
- PyMySQL
- Jinja2
- HTML
- CSS
- JavaScript

Use Python with direct MySQL access through PyMySQL.

Do NOT introduce:

- SQLAlchemy
- Alembic
- PostgreSQL
- SQLite
- MongoDB
- Redis
- Another ORM
- Another database system

MySQL must be the only database used by the project.

---

# 4. Database Architecture

The database communication flow should be:

FastAPI
↓
Python
↓
PyMySQL
↓
MySQL

The application should not contain database credentials directly in source code.

The database connection should be configured using environment variables.

Example:

DATABASE_URL=mysql+pymysql://username:password@localhost:3306/finzo_dev

The actual credentials must NOT be committed to Git.

---

# 5. Development and Production Databases

Development and production databases must be separate.

Development database:

    finzo_dev

Production database:

    finzo_production

The application must not hardcode the database name.

The database connection should come from:

    DATABASE_URL

For local development, the `.env` file may contain the development database URL.

Example:

    DATABASE_URL=mysql+pymysql://root:password@localhost:3306/finzo_dev

The `.env` file must be included in `.gitignore`.

A `.env.example` file may be provided without real credentials.

Example:

    DATABASE_URL=mysql+pymysql://username:password@localhost:3306/finzo_dev

---

# 6. Database File Structure

The database implementation should use a simple structure that is easy to understand.

Recommended structure:

    database/
    ├── db.py
    └── models.py

If the existing project already has suitable files for database configuration or models, reuse them instead of creating duplicate files.

The database configuration file should contain:

- MySQL connection helper
- Cursor/connection management
- Query execution helpers
- Database initialization helper
- Seed helper

The models file should contain:

- User table contract
- Expense table contract

Database code should not contain application business logic.

---

# 7. Database Connection

The application must use Python with PyMySQL to connect to MySQL.

The connection URL must come from:

    DATABASE_URL

Do not hardcode:

- username
- password
- host
- port
- database name
- connection URL

Example:

    DATABASE_URL=mysql+pymysql://root:password@localhost:3306/finzo_dev

The implementation should open a MySQL connection, run a prepared SQL statement, and close the connection cleanly.

The implementation should handle database connection errors clearly so development problems can be diagnosed easily.

---

# 8. Direct MySQL Database Configuration

The database configuration should provide:

- A Python MySQL connection helper
- A function to get a connection or cursor
- A safe query execution pattern
- Database initialization helpers
- Seed functions

Conceptual structure:

    get_connection()
        ↓
    execute_query()
        ↓
    init_db()
        ↓
    seed_db()
        ↓
    FastAPI routes/services/repositories

Connections should be opened only when needed and closed after use.

The implementation should avoid creating unnecessary duplicate connections.

A single connection pattern should be reused by the application.

---

# 9. Database Schema

The initial Finzo database contains two tables:

1. `users`
2. `expenses`

The schema should remain simple and closely follow the existing application requirements.

---

# 10. Users Table

The `users` table represents registered Finzo users.

Required fields:

| Column | Type | Constraints |
|---|---|---|
| id | Integer | Primary key |
| email | String | NOT NULL, UNIQUE |
| password_hash | String/Text | NOT NULL |

Requirements:

- `id` must uniquely identify each user.
- `email` must be unique.
- `email` cannot be NULL.
- `password_hash` cannot be NULL.
- Passwords must never be stored as plain text.
- The demo user must contain a hashed password.
- The database should enforce the unique email constraint.

The database schema should define constraints directly in MySQL.

---

# 11. Expenses Table

The `expenses` table stores expenses belonging to users.

Required fields:

| Column | Type | Constraints |
|---|---|---|
| id | Integer | Primary key |
| user_id | Integer | NOT NULL, foreign key |
| amount | Numeric/Decimal | NOT NULL |
| category | String | NOT NULL |
| description | Text | Optional |
| expense_date | Date | NOT NULL |

Requirements:

- `id` must uniquely identify an expense.
- `user_id` must reference an existing user.
- `amount` cannot be NULL.
- `category` cannot be NULL.
- `expense_date` cannot be NULL.
- An expense cannot belong to a nonexistent user.

The MySQL schema should define the foreign key relationship.

---

# 12. Foreign Key Requirements

The database must enforce the relationship:

    expenses.user_id
            ↓
        users.id

An expense must always belong to a valid user.

For example:

    user_id = 1

is valid only if:

    users.id = 1

exists.

Inserting an expense with a nonexistent user ID must fail because of the foreign key constraint.

Do not rely only on application-level validation.

MySQL must enforce this relationship through the database schema.

Use an appropriate MySQL storage engine such as InnoDB so foreign key constraints are enforced.

---

# 13. Database Initialization

The application should initialize the required database tables safely.

The initialization process should:

- Connect to MySQL.
- Create the required tables if they do not already exist.
- Create the required constraints.
- Complete successfully when the tables already exist.
- Be safe to run multiple times.

Use explicit MySQL CREATE TABLE IF NOT EXISTS statements in Python.

The initialization process must not:

- Delete existing tables.
- Delete existing data.
- Recreate/reset the database every time the application starts.

Database initialization should only create missing tables.

---

# 14. Seed Data Requirements

A seed function is responsible for inserting demo data for development/testing.

The seed data must contain:

- 1 demo user
- 8 sample expenses
- Expenses distributed across different categories

The demo user's password must be stored as a hashed password.

The seed function must be idempotent.

This means:

    seed_db()

can be executed multiple times without creating duplicate demo users or duplicate sample expenses.

For example:

First execution:

    1 demo user
    8 expenses

Second execution:

    still 1 demo user
    still 8 expenses

Third execution:

    still 1 demo user
    still 8 expenses

The implementation must check whether the demo data already exists before inserting it.

Do not rely only on application assumptions to prevent duplicates.

---

# 15. Demo User

Create one demo user for development.

Example:

    Email:
    demo@finzo.com

The exact password may be specified by the implementation if necessary, but the password must never be stored directly in the database.

Only the password hash should be stored.

The seed process should create the password hash before inserting the user.

The demo user's email should be protected by the database's UNIQUE constraint.

Use the project's existing password hashing approach if one already exists.

If no password hashing implementation exists yet, use a secure password hashing library rather than storing a plain-text password.

Do not implement the complete authentication system as part of this task.

---

# 16. Sample Expenses

Create 8 demo expenses.

The expenses should cover multiple categories.

Example categories may include:

- Food
- Transport
- Shopping
- Bills
- Entertainment
- Health
- Education
- Other

The exact sample values can be reasonable development/demo values.

All 8 expenses must belong to the demo user.

The seed process must not create duplicate expenses when executed repeatedly.

---

# 17. Database Operations

Use Python and PyMySQL for database operations.

Do not manually construct SQL using string concatenation when values are user-controlled.

Prefer explicit SQL statements such as:

- `SELECT ... WHERE ...`
- `INSERT INTO ... VALUES ...`
- `UPDATE ... SET ... WHERE ...`
- `DELETE FROM ... WHERE ...`
- `cursor.execute(...)`
- `connection.commit()`
- `connection.rollback()`

Use parameterized queries for any variable values.

Do not create unsafe SQL strings using user-controlled values.

---

# 18. Database Constraints

MySQL must enforce the following:

### Primary keys

Both tables must have primary keys.

    users.id

    expenses.id

### Unique email

The following must fail when the email already exists:

    demo@finzo.com

The database should enforce this using a UNIQUE constraint.

### Foreign key

An expense with a nonexistent user ID must fail.

For example, if user `999` does not exist:

    expenses.user_id = 999

must be rejected by MySQL.

### NOT NULL

Required fields must not accept NULL values.

---

# 19. Error Handling Expectations

The database implementation should allow database errors to be identified clearly during development.

Expected behavior:

### Duplicate email

Attempting to insert a duplicate email should fail because of the MySQL UNIQUE constraint.

### Invalid user ID

Attempting to insert an expense with a nonexistent `user_id` should fail because of the MySQL FOREIGN KEY constraint.

### Database errors

Database errors should not be silently ignored.

Transactions should be rolled back when an operation fails and the connection remains usable.

Use explicit exception handling around MySQL operations.

Do not hide the original database error during development.

---

# 20. Application Startup

The database setup should integrate with the existing FastAPI application without breaking the current application.

If the existing application already has an application startup mechanism, use it rather than creating a conflicting startup system.

The startup process may:

1. Load environment configuration.
2. Initialize the MySQL database.
3. Create missing tables.
4. Run seed logic for development if required.

The implementation must not destroy existing database data during startup.

Do not recreate or reset tables on every application startup.

---

# 21. Environment Variables

Use environment variables for configuration.

Required:

    DATABASE_URL

Example development configuration:

    DATABASE_URL=mysql+pymysql://root:password@localhost:3306/finzo_dev

Do not commit actual credentials.

`.env` should be ignored by Git.

Example `.gitignore` entry:

    .env

An `.env.example` file may be included:

    DATABASE_URL=mysql+pymysql://username:password@localhost:3306/finzo_dev

---

# 22. Security Requirements

The implementation must:

- Never hardcode database credentials.
- Never store plain-text passwords.
- Use hashed passwords for demo users.
- Use parameterized SQL queries.
- Use MySQL constraints for data integrity.
- Keep `.env` out of Git.
- Never print database passwords or connection credentials in logs.
- Never expose database credentials through API responses.

---

# 23. Validation Requirements

After implementation, verify the following.

### Database connection

- MySQL is running.
- `DATABASE_URL` is loaded correctly.
- PyMySQL can connect successfully.

### Schema

- `users` table exists.
- `expenses` table exists.
- Primary keys exist.
- Unique email constraint exists.
- Foreign key constraint exists.
- Required NOT NULL constraints exist.

### Initialization

Run the database initialization.

Then run it again.

Expected:

    No error.

    Existing data is not deleted.

### Seeding

Run:

    seed_db()

Then run it again.

Expected:

    No duplicate demo user.

    No duplicate sample expenses.

### Foreign key

Attempt to insert an expense with an invalid user ID.

Expected:

    MySQL rejects the insert.

### Unique email

Attempt to insert the same email twice.

Expected:

    MySQL rejects the duplicate email.

### Password

Check the demo user's stored password.

Expected:

    The database contains a password hash.

    The database does not contain the plain-text password.

### Database connections

Verify that MySQL connections are properly closed after use.

---

# 24. Definition of Done

The database setup is considered complete when all of the following are true:

- [ ] MySQL development database `finzo_dev` is configured.
- [ ] Application connects using `DATABASE_URL`.
- [ ] No database credentials are hardcoded.
- [ ] MySQL connection helper is configured correctly.
- [ ] Connection and cursor management works correctly.
- [ ] FastAPI can obtain a database connection or query helper.
- [ ] `users` table exists with the required schema.
- [ ] `expenses` table exists with the required schema.
- [ ] Both tables have primary keys.
- [ ] Users have a UNIQUE email constraint.
- [ ] Expenses have a valid foreign key to users.
- [ ] Required NOT NULL constraints exist.
- [ ] Database initialization creates missing tables safely.
- [ ] Database initialization can be executed repeatedly without failure.
- [ ] Database initialization does not delete existing data.
- [ ] Seed logic creates one demo user.
- [ ] Demo user's password is stored as a hash.
- [ ] Seed logic creates 8 sample expenses.
- [ ] Sample expenses cover multiple categories.
- [ ] All sample expenses belong to the demo user.
- [ ] Seed logic can be executed repeatedly without duplicate data.
- [ ] Duplicate email insertion is rejected by MySQL.
- [ ] Invalid `user_id` insertion is rejected by MySQL.
- [ ] Database errors are not silently ignored.
- [ ] `.env` is excluded from Git.
- [ ] FastAPI starts without database-related errors.
- [ ] Existing Finzo functionality is not broken.

---

# 25. Out of Scope

Do NOT implement the following as part of this task:

- User registration
- User login
- Logout
- Authentication middleware
- Session management
- Password reset
- Expense CRUD endpoints
- Dashboard
- Budget tracking
- Charts
- AI assistant
- AI expense categorization
- Financial recommendations
- React frontend
- PostgreSQL
- SQLite
- MongoDB
- Redis
- SQLAlchemy
- Alembic
- ORM abstraction
- Database migration framework
- Production deployment

These features will be handled in separate tasks.

---

# 26. Implementation Principle

Keep the database implementation simple and understandable.

The goal of this task is to establish a reliable MySQL foundation for Finzo.

Prefer:

    FastAPI
        ↓
    Python
        ↓
    PyMySQL
        ↓
    MySQL

Avoid unnecessary abstractions.

Use explicit Python database code instead of introducing another ORM or database abstraction.

Every database operation should be understandable by reading the Python code and SQL statements.

Do not introduce SQLAlchemy, Alembic, or another ORM as part of this task.

---

# 27. Final Validation

Before considering the task complete, review the implementation against this specification.

Confirm:

1. MySQL is being used.
2. Python is communicating directly with MySQL through PyMySQL.
3. `DATABASE_URL` is used.
4. Connection and query helpers work correctly.
5. Database initialization is idempotent.
6. Seed logic is idempotent.
7. The users schema is correct.
8. The expenses schema is correct.
9. Unique email is enforced by MySQL.
10. Foreign key relationships are enforced by MySQL.
11. Passwords are hashed.
12. Eight demo expenses exist.
13. MySQL connections are properly managed.
14. No unrelated features were implemented.
15. Existing Finzo functionality still works.

The implementation should only be considered complete after all applicable checks pass.