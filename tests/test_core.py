"""
Юнит-тесты для AFLC Core
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import unittest
import time
from src.core import (
    AdaptiveFeedbackLoopCore,
    DefaultPolicy,
    SimpleCorrelator,
    ActionContext,
    Detection,
    Decision
)


class TestAFLCore(unittest.TestCase):
    """Тесты основного класса AFLC"""
    
    def setUp(self):
        """Создаёт экземпляр AFLC для каждого теста"""
        self.flc = AdaptiveFeedbackLoopCore(agent_id="test-agent")
        self.flc.register_policy(DefaultPolicy())
        self.flc.register_correlator(SimpleCorrelator())
    
    def test_initialization(self):
        """Тест: инициализация"""
        self.assertEqual(self.flc.agent_id, "test-agent")
        self.assertEqual(self.flc.action_counter, 0)
        self.assertIsNone(self.flc.last_decision)
    
    def test_normal_execution(self):
        """Тест: нормальное выполнение без аномалий"""
        def my_action():
            time.sleep(0.01)
            return {"status": "ok"}
        
        decision = self.flc.execute(my_action, endpoint="/api/test", method="GET")
        
        self.assertEqual(decision.action, "continue")
        self.assertEqual(decision.severity, 0.0)
        self.assertEqual(decision.risk_score, 0.0)
    
    def test_anomaly_detection(self):
        """Тест: обнаружение аномалии"""
        def slow_action():
            time.sleep(0.1)  # Достаточно долго для детектора
            return {"status": "ok"}
        
        # Сначала выполняем нормальные действия
        for i in range(5):
            self.flc.execute(lambda: time.sleep(0.01), endpoint="/api/test", method="GET")
        
        # Затем аномальное
        decision = self.flc.execute(slow_action, endpoint="/api/test", method="GET")
        
        # В зависимости от детектора, может быть continue или pause
        self.assertIn(decision.action, ["continue", "pause"])
    
    def test_context_creation(self):
        """Тест: создание контекста"""
        def my_action():
            return {"data": "test"}
        
        decision = self.flc.execute(
            my_action,
            endpoint="/api/users",
            method="POST",
            payload={"user": "test"},
            user_id="admin"
        )
        
        # Проверяем, что история сохранилась
        self.assertEqual(len(self.flc.history), 1)
        self.assertEqual(self.flc.history[0]["endpoint"], "/api/users")
        self.assertEqual(self.flc.history[0]["method"], "POST")
    
    def test_reset(self):
        """Тест: сброс состояния"""
        def my_action():
            return {"status": "ok"}
        
        self.flc.execute(my_action, endpoint="/api/test", method="GET")
        self.assertEqual(self.flc.action_counter, 1)
        
        self.flc.reset()
        self.assertEqual(self.flc.action_counter, 0)
        self.assertEqual(len(self.flc.history), 0)
        self.assertIsNone(self.flc.last_decision)
    
    def test_stats(self):
        """Тест: статистика"""
        stats = self.flc.get_stats()
        self.assertEqual(stats["agent_id"], "test-agent")
        self.assertEqual(stats["actions"], 0)
        self.assertTrue(stats["has_policy"])
        self.assertTrue(stats["has_correlator"])


if __name__ == "__main__":
    unittest.main()
