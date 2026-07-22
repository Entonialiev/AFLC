"""
History Backend for AFLC
Version: 2.0.0 (with ABC)
"""

from typing import Dict, List, Optional, Any
import json
import sqlite3
import time
from collections import deque
import logging

from .interfaces import HistoryBackend

logger = logging.getLogger("aflc.history")


class MemoryHistory(HistoryBackend):
    """In-memory реализация с ограничением размера"""
    
    def __init__(self, config: Optional[Dict] = None):
        config = config or {}
        self.max_size = config.get("max_size", 10000)
        self.storage_file = config.get("storage_file", None)
        self._records: deque = deque(maxlen=self.max_size)
        self._load()
    
    def _load(self):
        if self.storage_file:
            try:
                with open(self.storage_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self._records.extend(data)
            except (FileNotFoundError, json.JSONDecodeError) as e:
                logger.debug(f"Loading history: {e}")
    
    def _save(self):
        if self.storage_file:
            with open(self.storage_file, 'w', encoding='utf-8') as f:
                json.dump(list(self._records), f, ensure_ascii=False)
    
    def add(self, record: Dict[str, Any]) -> None:
        self._records.append(record)
        self._save()
    
    def get_recent(self, limit: int = 10) -> List[Dict[str, Any]]:
        return list(self._records)[-limit:]
    
    def get_stats(self) -> Dict[str, Any]:
        return {
            "total": len(self._records),
            "max_size": self.max_size,
            "type": "memory",
            "storage_file": self.storage_file
        }
    
    def clear(self) -> None:
        self._records.clear()
        if self.storage_file:
            self._save()


class SQLiteHistory(HistoryBackend):
    """SQLite реализация для постоянного хранения"""
    
    def __init__(self, config: Optional[Dict] = None):
        config = config or {}
        self.db_path = config.get("db_path", "aflc_history.db")
        self.max_records = config.get("max_records", 100000)
        self._init_db()
    
    def _init_db(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp REAL,
                    action_id TEXT,
                    endpoint TEXT,
                    method TEXT,
                    latency_ms REAL,
                    error_code INTEGER,
                    decision TEXT,
                    severity REAL,
                    risk_score REAL,
                    metadata TEXT
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_timestamp ON history(timestamp)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_endpoint ON history(endpoint)")
    
    def add(self, record: Dict[str, Any]) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO history (
                    timestamp, action_id, endpoint, method,
                    latency_ms, error_code, decision, severity,
                    risk_score, metadata
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                record.get("timestamp", time.time()),
                record.get("action_id", ""),
                record.get("endpoint", ""),
                record.get("method", "GET"),
                record.get("latency_ms", 0.0),
                record.get("error_code", 0),
                record.get("decision", ""),
                record.get("severity", 0.0),
                record.get("risk_score", 0.0),
                json.dumps(record.get("metadata", {}))
            ))
            conn.execute(
                "DELETE FROM history WHERE id NOT IN (SELECT id FROM history ORDER BY timestamp DESC LIMIT ?)",
                (self.max_records,)
            )
    
    def get_recent(self, limit: int = 10) -> List[Dict[str, Any]]:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT * FROM history ORDER BY timestamp DESC LIMIT ?", (limit,)
            )
            rows = cursor.fetchall()
            return [
                {
                    "id": row[0],
                    "timestamp": row[1],
                    "action_id": row[2],
                    "endpoint": row[3],
                    "method": row[4],
                    "latency_ms": row[5],
                    "error_code": row[6],
                    "decision": row[7],
                    "severity": row[8],
                    "risk_score": row[9],
                    "metadata": json.loads(row[10]) if row[10] else {}
                }
                for row in rows
            ]
    
    def get_stats(self) -> Dict[str, Any]:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT COUNT(*) FROM history")
            total = cursor.fetchone()[0]
            return {
                "total": total,
                "db_path": self.db_path,
                "max_records": self.max_records,
                "type": "sqlite"
            }
    
    def clear(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM history")
            conn.execute("VACUUM")
