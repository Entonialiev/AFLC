"""
Простая демонстрация работы AFLC
"""

import sys
import time
sys.path.append('../src')

from core import AdaptiveFeedbackLoopCore, DefaultPolicy
from detectors.rule import RuleDetector


def main():
    print("🔁 AFLC Demo")
    print("-" * 40)
    
    # Создаём AFLC с детектором и политикой
    flc = (
        AdaptiveFeedbackLoopCore(agent_id="demo-agent")
        .register_detector(RuleDetector())
        .register_policy(DefaultPolicy())
    )
    
    def my_action():
        time.sleep(0.05)
        return {"status": "ok"}
    
    # Выполняем 10 нормальных действий
    print("🟢 Нормальные действия:")
    for i in range(8):
        decision = flc.execute(my_action, endpoint="/api/test", method="GET")
        print(f"  {i+1}: {decision.action} (severity: {decision.severity:.2f})")
    
    # Аномальное действие (долгая задержка)
    def slow_action():
        time.sleep(3.0)
        return {"status": "ok"}
    
    print("\n🔴 Аномальное действие (таймаут 3с):")
    decision = flc.execute(slow_action, endpoint="/api/test", method="GET")
    print(f"  Результат: {decision.action}")
    print(f"  Причина: {decision.reason}")
    print(f"  Severity: {decision.severity:.2f}")
    print(f"  Риск: {decision.risk_score:.2f}")


if __name__ == "__main__":
    main()
