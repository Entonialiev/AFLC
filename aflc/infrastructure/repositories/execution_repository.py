"""
Execution Repository implementation using SQLite
"""

import json
from typing import Optional, List, Dict, Any
from datetime import datetime
import sqlite3

from aflc.domain.execution import Execution
from aflc.domain.value_objects import (
    Action, Command, Observation, Finding, RiskScore, Explanation
)
from aflc.domain.enums import ExecutionStatus, DecisionAction
from aflc.application.interfaces import ExecutionRepository


class SQLiteExecutionRepository(ExecutionRepository):
    """SQLite implementation of ExecutionRepository."""

    def __init__(self, db_path: str = "aflc.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self) -> None:
        """Initialize database tables."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS executions (
                    execution_id TEXT PRIMARY KEY,
                    status TEXT NOT NULL,
                    action TEXT NOT NULL,
                    command TEXT NOT NULL,
                    observations TEXT,
                    findings TEXT,
                    risk_score TEXT,
                    decision TEXT,
                    explanation TEXT,
                    context TEXT,
                    created_at TIMESTAMP,
                    updated_at TIMESTAMP
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_executions_status 
                ON executions(status)
            """)

    def _serialize_execution(self, execution: Execution) -> Dict[str, Any]:
        """Serialize Execution to dict for storage."""
        # Сериализуем decision, обрабатывая Enum
        decision_data = None
        if execution.decision:
            decision_data = {
                "action": execution.decision["action"].value if isinstance(execution.decision["action"], DecisionAction) else execution.decision["action"],
                "reason": execution.decision["reason"],
                "severity": execution.decision["severity"]
            }

        return {
            "execution_id": execution.execution_id,
            "status": execution.status.value,
            "action": {
                "action_id": execution.action.action_id,
                "agent_id": execution.action.agent_id,
                "endpoint": execution.action.endpoint,
                "method": execution.action.method,
                "payload": execution.action.payload,
                "timestamp": execution.action.timestamp.isoformat()
            },
            "command": {
                "command_id": execution.command.command_id,
                "type": execution.command.type,
                "payload": execution.command.payload,
                "timestamp": execution.command.timestamp.isoformat(),
                "idempotency_key": execution.command.idempotency_key
            },
            "observations": [
                {
                    "observation_id": o.observation_id,
                    "metric": o.metric,
                    "value": o.value,
                    "timestamp": o.timestamp.isoformat()
                }
                for o in execution.observations
            ],
            "findings": [
                {
                    "source": f.source,
                    "score": f.score,
                    "confidence": f.confidence,
                    "reason": f.reason,
                    "tags": list(f.tags)
                }
                for f in execution.findings
            ],
            "risk_score": {
                "value": execution.risk_score.value,
                "confidence": execution.risk_score.confidence,
                "components": execution.risk_score.components
            } if execution.risk_score else None,
            "decision": decision_data,
            "explanation": {
                "text": execution.explanation.text,
                "details": execution.explanation.details
            } if execution.explanation else None,
            "context": execution.context.to_dict() if execution.context else None,
            "created_at": execution.created_at.isoformat(),
            "updated_at": execution.updated_at.isoformat()
        }

    def _deserialize_execution(self, data: Dict[str, Any]) -> Execution:
        """Deserialize Execution from dict."""
        # Создаём Action
        action = Action(
            action_id=data["action"]["action_id"],
            agent_id=data["action"]["agent_id"],
            endpoint=data["action"]["endpoint"],
            method=data["action"]["method"],
            payload=data["action"]["payload"],
            timestamp=datetime.fromisoformat(data["action"]["timestamp"])
        )

        # Создаём Command
        command = Command(
            command_id=data["command"]["command_id"],
            type=data["command"]["type"],
            payload=data["command"]["payload"],
            timestamp=datetime.fromisoformat(data["command"]["timestamp"]),
            idempotency_key=data["command"].get("idempotency_key")
        )

        # Создаём Execution
        execution = Execution(action, command)
        execution.execution_id = data["execution_id"]
        execution.status = ExecutionStatus(data["status"])
        execution.created_at = datetime.fromisoformat(data["created_at"])
        execution.updated_at = datetime.fromisoformat(data["updated_at"])

        # Восстанавливаем observations
        for obs_data in data.get("observations", []):
            observation = Observation(
                observation_id=obs_data["observation_id"],
                metric=obs_data["metric"],
                value=obs_data["value"],
                timestamp=datetime.fromisoformat(obs_data["timestamp"])
            )
            execution.observations.append(observation)

        # Восстанавливаем findings
        for find_data in data.get("findings", []):
            finding = Finding(
                source=find_data["source"],
                score=find_data["score"],
                confidence=find_data["confidence"],
                reason=find_data["reason"],
                tags=tuple(find_data["tags"])
            )
            execution.findings.append(finding)

        # Восстанавливаем risk_score
        if data.get("risk_score"):
            execution.risk_score = RiskScore(
                value=data["risk_score"]["value"],
                confidence=data["risk_score"]["confidence"],
                components=data["risk_score"]["components"]
            )

        # Восстанавливаем decision
        if data.get("decision"):
            execution.decision = {
                "action": DecisionAction(data["decision"]["action"]),
                "reason": data["decision"]["reason"],
                "severity": data["decision"]["severity"]
            }

        # Восстанавливаем explanation
        if data.get("explanation"):
            execution.explanation = Explanation(
                text=data["explanation"]["text"],
                details=data["explanation"]["details"]
            )

        return execution

    def save(self, execution: Execution) -> None:
        """Save execution to database."""
        data = self._serialize_execution(execution)
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO executions (
                    execution_id, status, action, command,
                    observations, findings, risk_score, decision,
                    explanation, context, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                data["execution_id"],
                data["status"],
                json.dumps(data["action"]),
                json.dumps(data["command"]),
                json.dumps(data["observations"]),
                json.dumps(data["findings"]),
                json.dumps(data["risk_score"]),
                json.dumps(data["decision"]),
                json.dumps(data["explanation"]),
                json.dumps(data["context"]),
                data["created_at"],
                data["updated_at"]
            ))

    def find_by_id(self, execution_id: str) -> Optional[Execution]:
        """Find execution by ID."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT * FROM executions WHERE execution_id = ?",
                (execution_id,)
            )
            row = cursor.fetchone()
            if not row:
                return None

            data = {
                "execution_id": row[0],
                "status": row[1],
                "action": json.loads(row[2]),
                "command": json.loads(row[3]),
                "observations": json.loads(row[4]) if row[4] else [],
                "findings": json.loads(row[5]) if row[5] else [],
                "risk_score": json.loads(row[6]) if row[6] else None,
                "decision": json.loads(row[7]) if row[7] else None,
                "explanation": json.loads(row[8]) if row[8] else None,
                "context": json.loads(row[9]) if row[9] else None,
                "created_at": row[10],
                "updated_at": row[11]
            }
            return self._deserialize_execution(data)

    def find_by_status(self, status: str) -> List[Execution]:
        """Find all executions with given status."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT * FROM executions WHERE status = ?",
                (status,)
            )
            rows = cursor.fetchall()
            executions = []
            for row in rows:
                data = {
                    "execution_id": row[0],
                    "status": row[1],
                    "action": json.loads(row[2]),
                    "command": json.loads(row[3]),
                    "observations": json.loads(row[4]) if row[4] else [],
                    "findings": json.loads(row[5]) if row[5] else [],
                    "risk_score": json.loads(row[6]) if row[6] else None,
                    "decision": json.loads(row[7]) if row[7] else None,
                    "explanation": json.loads(row[8]) if row[8] else None,
                    "context": json.loads(row[9]) if row[9] else None,
                    "created_at": row[10],
                    "updated_at": row[11]
                }
                executions.append(self._deserialize_execution(data))
            return executions

    def find_all(self) -> List[Execution]:
        """Find all executions."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT * FROM executions")
            rows = cursor.fetchall()
            executions = []
            for row in rows:
                data = {
                    "execution_id": row[0],
                    "status": row[1],
                    "action": json.loads(row[2]),
                    "command": json.loads(row[3]),
                    "observations": json.loads(row[4]) if row[4] else [],
                    "findings": json.loads(row[5]) if row[5] else [],
                    "risk_score": json.loads(row[6]) if row[6] else None,
                    "decision": json.loads(row[7]) if row[7] else None,
                    "explanation": json.loads(row[8]) if row[8] else None,
                    "context": json.loads(row[9]) if row[9] else None,
                    "created_at": row[10],
                    "updated_at": row[11]
                }
                executions.append(self._deserialize_execution(data))
            return executions
