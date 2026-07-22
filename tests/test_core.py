"""
Юнит-тесты для AFLC Core
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import unittest
from src.core import AdaptiveFeedbackLoopCore
from src.defaults import DefaultPolicy, SimpleCorrelator


class TestAFLCore(unittest.TestCase):
    
    def setUp(self):
        self.flc = AdaptiveFeedbackLoopCore(agent_id="test-agent")
        self.flc.register_policy(DefaultPolicy())
        self.flc.register_correlator(SimpleCorrelator())
    
    def test_initialization(self):
        self.assertEqual(self.flc.agent_id, "test-agent")
        self.assertEqual(self.flc.action_counter, 0)
    
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
    
    def test_stats(self):
        stats = self.flc.get_stats()
        self.assertEqual(stats["agent_id"], "test-agent")
        self.assertTrue(stats["has_policy"])
        self.assertTrue(stats["has_correlator"])
