"""
Юнит-тесты для AFLC Core
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import unittest
import time
from src.core import AdaptiveFeedbackLoopCore
from src.defaults import DefaultPolicy, SimpleCorrelator
from src.models import ActionContext, Detection, Decision
from src.interfaces import Detector


class TestAFLCore(unittest.TestCase):
    """Тесты основного класса AFLC"""
    
    def setUp(self):
        self.flc = AdaptiveFeedbackLoopCore(agent_id="test-agent")
        self.flc.register_policy(DefaultPolicy())
        self.flc.register_correlator(SimpleCorrelator())
    
    def test_initialization(self):
        self.assertEqual(self.flc.agent_id, "test-agent")
        self.assertEqual(self.flc.action_counter, 0)
        self.assertIsNone(self.flc.last_decision)
    
    def test_normal_execution(self):
        def my_action():
            return {"status": "ok"}
        
        decision = self.flc.execute(my_action, endpoint="/api/test", method="GET")
        self.assertEqual(decision.action, "continue")
        self.assertEqual(decision.severity, 0.0)
        self.assertEqual(decision.risk_score, 0.0)
    
    def test_context_creation(self):
        def my_action():
            return {"data": "test"}
        
        decision = self.flc.execute(
            my_action,
            endpoint="/api/users",
            method="POST",
            payload={"user": "test"},
            user_id="admin"
        )
        self.assertIsNotNone(decision)
        self.assertIn(decision.action, ["continue", "pause"])
    
    def test_reset(self):
        def my_action():
            return {"status": "ok"}
        
        self.flc.execute(my_action, endpoint="/api/test", method="GET")
        self.assertEqual(self.flc.action_counter, 1)
        
        self.flc.reset()
        self.assertEqual(self.flc.action_counter, 0)
        self.assertIsNone(self.flc.last_decision)
    
    def test_stats(self):
        stats = self.flc.get_stats()
        self.assertEqual(stats["agent_id"], "test-agent")
        self.assertEqual(stats["actions"], 0)
        self.assertTrue(stats["has_policy"])
        self.assertTrue(stats["has_correlator"])
    
    def test_config_load(self):
        config_path = os.path.join(os.path.dirname(__file__), '..', 'config.yaml')
        if os.path.exists(config_path):
            flc = AdaptiveFeedbackLoopCore.from_config(config_path)
            self.assertEqual(flc.agent_id, "demo-agent")


if __name__ == "__main__":
    unittest.main()
