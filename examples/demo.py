"""
AFLC Demo — Full Pipeline with Risk Engine
"""

import sys
import time
import random
sys.path.append('../src')

from core import AdaptiveFeedbackLoopCore, DefaultPolicy
from detectors import RuleDetector, StatisticalDetector
from correlator import Correlator
from risk import RiskEngine


def main():
    print("🔁 AFLC Demo — Full Pipeline with Risk Engine")
    print("-" * 60)
    
    flc = (
        AdaptiveFeedbackLoopCore(agent_id="demo-agent")
        .register_detector(RuleDetector())
        .register_detector(StatisticalDetector(config={"z_score_threshold": 2.5}))
        .register_correlator(Correlator(config={"strategy": "weighted"}))
        .register_risk_engine(RiskEngine())
        .register_policy(DefaultPolicy())
    )
    
    def my_action(delay=0.05, size=1024):
        time.sleep(delay)
        return {"status": "ok", "data": "x" * size}
    
    # Фаза обучения
    print("\n📚 Фаза обучения (30 запросов)...")
    for i in range(30):
        delay = random.uniform(0.04, 0.08)
        flc.execute(my_action, delay, size=1024, endpoint="/api/users", method="GET")
    
    print("✅ Обучение завершено\n")
    
    # Сценарии
    scenarios = [
        ("/api/public", "GET", "guest", 0.05, "🟢 Низкий риск"),
        ("/api/users", "POST", "user", 0.3, "🟡 Средний риск"),
        ("/api/admin/delete", "DELETE", "admin", 0.3, "🔴 Высокий риск"),
        ("/api/admin/delete", "DELETE", "admin", 3.0, "🔴 Критический риск")
    ]
    
    for endpoint, method, user, delay, risk_label in scenarios:
        decision = flc.execute(
            my_action, delay, size=1024,
            endpoint=endpoint,
            method=method,
            user_id=user
        )
        print(f"{risk_label}: {endpoint} [{method}] user={user}")
        print(f"  → {decision.action} (severity: {decision.severity:.2f}, risk: {decision.risk_score:.2f})")
        print(f"  Причина: {decision.reason}")
        print()
    
    print(f"📊 Статистика: {flc.get_stats()}")


if __name__ == "__main__":
    main()
