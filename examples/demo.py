"""
AFLC Demo — Full Pipeline with Memory
"""

import sys
import time
import random
sys.path.append('../src')

from core import AdaptiveFeedbackLoopCore, DefaultPolicy
from detectors import RuleDetector, StatisticalDetector
from correlator import Correlator
from risk import RiskEngine
from explainer import Explainer
from memory import Memory


def main():
    print("🔁 AFLC Demo — Full Pipeline with Memory")
    print("-" * 60)
    
    # Создаём Memory
    memory = Memory(storage_file="flc_memory.json", max_size=1000)
    
    flc = (
        AdaptiveFeedbackLoopCore(agent_id="demo-agent")
        .register_detector(RuleDetector())
        .register_detector(StatisticalDetector(config={"z_score_threshold": 2.5}))
        .register_correlator(Correlator(config={"strategy": "weighted"}))
        .register_risk_engine(RiskEngine())
        .register_policy(DefaultPolicy())
        .register_explainer(Explainer())
        .register_memory(memory)
    )
    
    def my_action(delay=0.05, size=1024):
        time.sleep(delay)
        return {"status": "ok", "data": "x" * size}
    
    # Фаза обучения
    print("📚 Фаза обучения (30 запросов)...")
    for i in range(30):
        delay = random.uniform(0.04, 0.08)
        flc.execute(my_action, delay, size=1024, endpoint="/api/users", method="GET")
    
    print("✅ Обучение завершено\n")
    
    # Аномальный запрос
    print("🔴 Критическая аномалия:")
    print("-" * 40)
    
    decision = flc.execute(
        my_action, 3.0, size=1024,
        endpoint="/api/admin/delete",
        method="DELETE",
        user_id="admin"
    )
    
    print(flc.explainer.explain(None, None, decision, None))
    
    # Статистика памяти
    print("\n📊 Статистика памяти:")
    stats = flc.memory.get_stats()
    print(f"  Всего записей: {stats['total_records']}")
    print(f"  Аномалий: {stats['anomalies']}")
    print(f"  Частота аномалий: {stats['anomaly_rate']:.2%}")


if __name__ == "__main__":
    main()
