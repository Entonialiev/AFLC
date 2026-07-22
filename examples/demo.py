"""
AFLC Demo — RuleDetector + StatisticalDetector + Correlator
"""

import sys
import time
import random
sys.path.append('../src')

from core import AdaptiveFeedbackLoopCore, DefaultPolicy
from detectors import RuleDetector, StatisticalDetector
from correlator import Correlator


def main():
    print("🔁 AFLC Demo — Full Pipeline")
    print("-" * 50)
    
    # Создаём AFLC со всеми компонентами
    flc = (
        AdaptiveFeedbackLoopCore(agent_id="demo-agent")
        .register_detector(RuleDetector())
        .register_detector(StatisticalDetector(config={"z_score_threshold": 2.5}))
        .register_correlator(Correlator(config={"strategy": "weighted"}))
        .register_policy(DefaultPolicy())
    )
    
    def my_action(delay=0.05, size=1024):
        time.sleep(delay)
        return {"status": "ok", "data": "x" * size}
    
    # Фаза обучения (30 нормальных запросов)
    print("\n📚 Фаза обучения (30 запросов)...")
    for i in range(30):
        delay = random.uniform(0.04, 0.08)
        flc.execute(my_action, delay, size=1024, endpoint="/api/users", method="GET")
    
    print("✅ Обучение завершено\n")
    
    # Нормальные запросы
    print("🟢 Нормальные запросы:")
    for i in range(5):
        delay = random.uniform(0.05, 0.07)
        decision = flc.execute(my_action, delay, size=1024, endpoint="/api/users", method="GET")
        print(f"  {i+1}: {decision.action} (severity: {decision.severity:.2f})")
    
    # Аномальные запросы
    print("\n🔴 Аномальные запросы:")
    
    # Аномалия 1: Сильная задержка
    print("  1. Сильная задержка (3000ms):")
    decision = flc.execute(my_action, 3.0, size=1024, endpoint="/api/users", method="GET")
    print(f"     → {decision.action}")
    print(f"     Причина: {decision.reason}")
    
    # Аномалия 2: Резкий скачок размера
    print("  2. Резкий скачок размера (100KB):")
    def big_action():
        time.sleep(0.05)
        return {"status": "ok", "data": "x" * 100000}
    decision = flc.execute(big_action, endpoint="/api/users", method="GET")
    print(f"     → {decision.action}")
    print(f"     Причина: {decision.reason}")
    
    # Статистика
    print(f"\n📊 Статистика:")
    print(f"  Всего действий: {flc.action_counter}")
    print(f"  Детекторов: {len(flc.detectors)}")


if __name__ == "__main__":
    main()
