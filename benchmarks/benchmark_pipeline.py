"""
AFLC Detection Pipeline Benchmark
"""

import pytest

from src.models import ActionContext, RiskScore
from src.defaults import DefaultPolicy, SimpleCorrelator
from src.detectors import RuleDetector


def create_test_context(latency_ms: float = 500, error_code: int = 0):
    """Создаёт тестовый контекст"""
    return ActionContext(
        action_id="benchmark",
        endpoint="/api/test",
        method="GET",
        latency_ms=latency_ms,
        error_code=error_code,
        response_size=1024,
        user_id="bench_user"
    )


def test_detector_only(benchmark):
    """Измеряет скорость одного детектора"""
    detector = RuleDetector({
        "latency_threshold": 200,
        "error_threshold": 5,
        "response_size_threshold": 10000
    })
    context = create_test_context(latency_ms=500)
    
    result = benchmark(detector.detect, context)
    
    # Детектор должен сработать (latency > 200)
    assert result is not None
    assert result.score > 0


def test_detector_without_anomaly(benchmark):
    """Измеряет скорость детектора без аномалии"""
    detector = RuleDetector({
        "latency_threshold": 200,
        "error_threshold": 5
    })
    context = create_test_context(latency_ms=100)  # Нормальная задержка
    
    result = benchmark(detector.detect, context)
    
    # Детектор не должен сработать
    assert result is None


def test_full_pipeline_no_detectors(benchmark):
    """Измеряет скорость пайплайна без детекторов"""
    from src.core import AdaptiveFeedbackLoopCore
    from src.history import MemoryHistory
    
    flc = AdaptiveFeedbackLoopCore(agent_id="bench")
    flc.register_policy(DefaultPolicy())
    flc.register_correlator(SimpleCorrelator())
    flc.register_history_backend(MemoryHistory({"max_size": 100}))
    
    def action():
        return {"status": "ok"}
    
    result = benchmark(
        flc.execute,
        action,
        endpoint="/api/test",
        method="GET"
    )
    
    assert result is not None
    assert result.action == "continue"


def test_full_pipeline_with_detector(benchmark):
    """Измеряет скорость полного пайплайна с детектором"""
    from src.core import AdaptiveFeedbackLoopCore
    from src.history import MemoryHistory
    
    flc = AdaptiveFeedbackLoopCore(agent_id="bench")
    flc.register_detector(RuleDetector({
        "latency_threshold": 200
    }))
    flc.register_policy(DefaultPolicy())
    flc.register_correlator(SimpleCorrelator())
    flc.register_history_backend(MemoryHistory({"max_size": 100}))
    
    def action():
        import time
        time.sleep(0.15)  # 150ms — аномалия
        return {"status": "ok"}
    
    result = benchmark(
        flc.execute,
        action,
        endpoint="/api/test",
        method="GET"
    )
    
    assert result is not None
    # Может быть pause или continue в зависимости от настроек


def test_correlator_speed(benchmark):
    """Измеряет скорость коррелятора"""
    from src.models import Detection
    
    correlator = SimpleCorrelator()
    
    detections = [
        Detection(source="a", score=0.7, confidence=0.9, reason="test"),
        Detection(source="b", score=0.8, confidence=0.8, reason="test"),
        Detection(source="c", score=0.6, confidence=0.9, reason="test"),
    ]
    
    result = benchmark(correlator.correlate, detections)
    
    assert result is not None
    assert result.score == 0.8  # Максимальный


def test_policy_speed(benchmark):
    """Измеряет скорость политики"""
    from src.models import Detection, RiskScore
    
    policy = DefaultPolicy({"pause_threshold": 0.3})
    context = create_test_context()
    detection = Detection(source="test", score=0.7, confidence=0.9, reason="test")
    risk = RiskScore(value=0.8, confidence=0.9)
    
    result = benchmark(
        policy.decide,
        context,
        detection,
        risk
    )
    
    assert result is not None
    assert result.action == "pause"
