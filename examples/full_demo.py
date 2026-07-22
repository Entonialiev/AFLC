#!/usr/bin/env python
"""
AFLC Full Demo — показывает полный жизненный цикл
"""

import sys
import os
import time
import json
from datetime import datetime

# Добавляем путь к проекту
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from aflc.bootstrap import create_aflc
from aflc.domain.enums import ExecutionStatus, DecisionAction


def main():
    print("=" * 60)
    print("🔁 AFLC Full Demo")
    print("=" * 60)

    # --- 1. Создаём AFLC ---
    print("\n📦 1. Инициализация AFLC...")
    aflc = create_aflc("demo.db", use_sqlite=True)
    engine = aflc.get_engine()
    event_bus = aflc.get_event_bus()

    print("✅ AFLC создан")

    # --- 2. Подписываемся на события ---
    print("\n📡 2. Подписка на события...")

    def on_execution_created(event):
        print(f"   📨 Событие: ExecutionCreated (id={event.execution_id})")

    def on_decision_made(event):
        print(f"   📨 Событие: DecisionMade (action={event.action.value})")

    event_bus.subscribe(DecisionAction.EXECUTION_CREATED, handler=on_execution_created)
    event_bus.subscribe(DecisionAction.DECISION_MADE, handler=on_decision_made)

    print("✅ Подписки созданы")

    # --- 3. Отправляем действие ---
    print("\n🚀 3. Отправка действия...")
    execution = engine.submit_action(
        agent_id="demo-agent",
        endpoint="/api/users/delete",
        method="DELETE",
        payload={"user_id": 123, "reason": "test"}
    )

    print(f"   Execution ID: {execution.execution_id}")
    print(f"   Status: {execution.status.value}")

    # --- 4. Переводим в состояние PENDING и RUNNING ---
    print("\n🔄 4. Перевод в состояние RUNNING...")
    execution.submit()
    execution.start_processing()
    print(f"   Status: {execution.status.value}")

    # --- 5. Добавляем наблюдения ---
    print("\n📊 5. Добавление наблюдений...")
    engine.add_observation(
        execution_id=execution.execution_id,
        metric="latency_ms",
        value=150.0
    )
    print("   ✅ Добавлено наблюдение: latency_ms=150ms")

    engine.add_observation(
        execution_id=execution.execution_id,
        metric="response_size",
        value=2048
    )
    print("   ✅ Добавлено наблюдение: response_size=2048b")

    # --- 6. Добавляем находки ---
    print("\n🔍 6. Добавление находок...")
    engine.add_finding(
        execution_id=execution.execution_id,
        source="rule",
        score=0.7,
        confidence=0.9,
        reason="High latency detected",
        tags=["performance", "latency"]
    )
    print("   ✅ Находка: High latency detected (score=0.7)")

    engine.add_finding(
        execution_id=execution.execution_id,
        source="statistical",
        score=0.8,
        confidence=0.85,
        reason="Response size anomaly",
        tags=["security", "size"]
    )
    print("   ✅ Находка: Response size anomaly (score=0.8)")

    # --- 7. Завершаем обработку ---
    print("\n⚙️ 7. Завершение обработки...")
    execution.complete_processing()
    print(f"   Status: {execution.status.value}")

    # --- 8. Оценка риска ---
    print("\n📈 8. Оценка риска...")
    engine.complete_assessment(
        execution_id=execution.execution_id,
        risk_value=0.85,
        confidence=0.9,
        components={
            "rule": 0.7,
            "statistical": 0.8,
            "endpoint": 0.9
        }
    )
    print("   ✅ Оценка риска: 0.85")

    # --- 9. Принятие решения ---
    print("\n⚖️ 9. Принятие решения...")
    engine.make_decision(
        execution_id=execution.execution_id,
        action="block",
        reason="High risk (0.85) exceeds threshold (0.3)",
        severity=0.85
    )
    print("   ✅ Решение: BLOCK")

    # --- 10. Объяснение ---
    print("\n📝 10. Генерация объяснения...")
    engine.add_explanation(
        execution_id=execution.execution_id,
        text="Action blocked due to high risk score (0.85). "
             "Detected anomalies: high latency (150ms) and abnormal response size (2048b). "
             "Endpoint /api/users/delete is critical.",
        details={
            "risk": 0.85,
            "threshold": 0.3,
            "anomalies": ["latency", "size"],
            "endpoint_criticality": 0.9
        }
    )
    print("   ✅ Объяснение добавлено")

    # --- 11. Архивация ---
    print("\n📦 11. Архивация...")
    engine.archive_execution(execution.execution_id)
    print(f"   ✅ Статус: {execution.status.value}")

    # --- 12. Получение Execution из репозитория ---
    print("\n📋 12. Получение Execution из репозитория...")
    saved = engine.get_execution(execution.execution_id)
    print(f"   Execution ID: {saved.execution_id}")
    print(f"   Status: {saved.status.value}")
    print(f"   Risk: {saved.risk_score.value if saved.risk_score else 'None'}")
    print(f"   Decision: {saved.decision['action'].value if saved.decision else 'None'}")

    # --- 13. Статистика ---
    print("\n📊 13. Статистика...")
    all_executions = engine.get_all_executions()
    print(f"   Всего Execution: {len(all_executions)}")

    by_status = {}
    for e in all_executions:
        status = e.status.value
        by_status[status] = by_status.get(status, 0) + 1

    for status, count in by_status.items():
        print(f"   - {status}: {count}")

    # --- Итог ---
    print("\n" + "=" * 60)
    print("✅ Демонстрация завершена!")
    print("   Все компоненты работают корректно")
    print("=" * 60)


if __name__ == "__main__":
    main()
