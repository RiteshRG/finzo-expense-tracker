from dataclasses import dataclass
from datetime import datetime


USER_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
"""

EXPENSE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS expenses (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    title VARCHAR(255) NOT NULL,
    amount DECIMAL(10, 2) NOT NULL,
    category VARCHAR(100) NOT NULL DEFAULT 'general',
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_expenses_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
"""


@dataclass
class User:
    id: int | None = None
    name: str = ""
    email: str = ""
    password_hash: str = ""
    created_at: datetime | None = None
    updated_at: datetime | None = None


@dataclass
class Expense:
    id: int | None = None
    user_id: int = 0
    title: str = ""
    amount: float = 0.0
    category: str = "general"
    description: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


__all__ = ["User", "Expense", "USER_TABLE_SQL", "EXPENSE_TABLE_SQL"]
