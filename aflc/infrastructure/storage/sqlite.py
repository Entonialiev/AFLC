"""
SQLite storage implementation
"""

import sqlite3
import json
from typing import Dict, Any, Optional, List, TypeVar, Generic
from dataclasses import dataclass, field
import logging

logger = logging.getLogger(__name__)

T = TypeVar('T')


@dataclass
class SQLiteStorage:
    """
    SQLite key-value storage.
    Uses JSON serialization for values.
    """

    db_path: str = "aflc.db"
    table_name: str = "storage"

    def __post_init__(self):
        self._init_db()

    def _init_db(self) -> None:
        """Initialize database table."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(f"""
                CREATE TABLE IF NOT EXISTS {self.table_name} (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.execute(f"""
                CREATE INDEX IF NOT EXISTS idx_{self.table_name}_key 
                ON {self.table_name}(key)
            """)

    def save(self, key: str, value: Any) -> None:
        """Save value by key."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(f"""
                INSERT OR REPLACE INTO {self.table_name} (key, value, updated_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
            """, (key, json.dumps(value, default=str)))

    def load(self, key: str) -> Optional[Any]:
        """Load value by key."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                f"SELECT value FROM {self.table_name} WHERE key = ?",
                (key,)
            )
            row = cursor.fetchone()
            if row:
                return json.loads(row[0])
            return None

    def delete(self, key: str) -> None:
        """Delete value by key."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                f"DELETE FROM {self.table_name} WHERE key = ?",
                (key,)
            )

    def list_keys(self, prefix: str = "") -> List[str]:
        """List all keys with given prefix."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                f"SELECT key FROM {self.table_name} WHERE key LIKE ?",
                (f"{prefix}%",)
            )
            return [row[0] for row in cursor.fetchall()]

    def clear(self) -> None:
        """Clear all data."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(f"DELETE FROM {self.table_name}")

    def count(self) -> int:
        """Return number of items."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(f"SELECT COUNT(*) FROM {self.table_name}")
            return cursor.fetchone()[0]

    def get_all(self) -> Dict[str, Any]:
        """Return all key-value pairs."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(f"SELECT key, value FROM {self.table_name}")
            return {row[0]: json.loads(row[1]) for row in cursor.fetchall()}
