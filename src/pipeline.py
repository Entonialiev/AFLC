"""
Pipeline for AFLC — единый конвейер выполнения действий
Version: 1.0.0
"""

from typing import List, Optional, Dict, Any, Callable
import time
import asyncio
import logging

from .core import (
    AdaptiveFeedbackLoopCore,
    ActionContext,
    Detection,
    Decision,
    RiskScore,
    Detector,
    AsyncDetector,
    Correlator,
    Policy,
    AsyncPolicy,
    Predictor,
    Memory,
    Explainer
)
from .events import EventBus, Event
from .exceptions import PipelineError, DetectorError

logger = logging.getLogger("aflc.pipeline")


class PipelineStep:
    """Базовый класс для шага пайплайна"""
    
    def execute(self, context: ActionContext, **kwargs) -> ActionContext:
        raise NotImplementedError
    
    async def execute_async(self, context: ActionContext, **kwargs) -> ActionContext:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.execute, context, **kwargs)


class SensorStep(PipelineStep):
    def __init__(self, core: AdaptiveFeedbackLoopCore):
        self.core = core
    
    def execute(self, context: ActionContext, **kwargs) -> ActionContext:
        return context


class DetectorStep(PipelineStep):
    def __init__(self, core: AdaptiveFeedbackLoopCore):
        self.core = core
    
    def execute(self, context: ActionContext, **kwargs) -> ActionContext:
        detections = []
        for detector in self.core.detectors:
            try:
                detection = detector.detect(context)
                if detection:
                    detections.append(detection)
            except Exception as e:
                logger.error(f"Detector error: {e}")
                raise DetectorError(f"Detector failed: {e}") from e
        
        context._detections = detections
        return context
    
    async def execute_async(self, context: ActionContext, **kwargs) -> ActionContext:
        detections = []
        for detector in self.core.detectors:
            try:
                if hasattr(detector, 'detect') and asyncio.iscoroutinefunction(detector.detect):
                    detection = await detector.detect(context)
                else:
                    detection = detector.detect(context)
                if detection:
                    detections.append(detection)
            except Exception as e:
                logger.error(f"Detector error: {e}")
                raise DetectorError(f"Detector failed: {e}") from e
        
        context._detections = detections
        return context


class CorrelatorStep(PipelineStep):
    def __init__(self, core: AdaptiveFeedbackLoopCore):
        self.core = core
    
    def execute(self, context: ActionContext, **kwargs) -> ActionContext:
        detections = getattr(context, '_detections', [])
        if self.core.correlator and detections:
            context._final_detection = self.core.correlator.correlate(detections)
        elif detections:
            context._final_detection = max(detections, key=lambda x: x.score)
        else:
            context._final_detection = None
        return context


class RiskStep(PipelineStep):
    def __init__(self, core: AdaptiveFeedbackLoopCore):
        self.core = core
    
    def execute(self, context: ActionContext, **kwargs) -> ActionContext:
        final_detection = getattr(context, '_final_detection', None)
        if self.core.risk_engine and final_detection:
            context._risk = self.core.risk_engine.evaluate(context, final_detection)
        else:
            if final_detection:
                context._risk = RiskScore(
                    value=final_detection.score,
                    confidence=final_detection.confidence,
                    components={"detection_score": final_detection.score}
                )
            else:
                context._risk = RiskScore(value=0.0, confidence=0.0)
        return context


class PolicyStep(PipelineStep):
    def __init__(self, core: AdaptiveFeedbackLoopCore):
        self.core = core
    
    def execute(self, context: ActionContext, **kwargs) -> ActionContext:
        final_detection = getattr(context, '_final_detection', None)
        risk = getattr(context, '_risk', RiskScore(value=0.0, confidence=0.0))
        
        if self.core.policy:
            if hasattr(self.core.policy, 'decide') and asyncio.iscoroutinefunction(self.core.policy.decide):
                raise RuntimeError("AsyncPolicy cannot be used in sync execute()")
            context._decision = self.core.policy.decide(context, final_detection, risk)
        else:
            if final_detection and final_detection.score > 0.3:
                context._decision = Decision(
                    action="pause",
                    reason=final_detection.reason,
                    severity=final_detection.score,
                    confidence=final_detection.confidence,
                    risk_score=risk.value,
                    explanation=f"Anomaly detected by {final_detection.source}"
                )
            else:
                context._decision = Decision(
                    action="continue",
                    reason="No anomalies detected",
                    severity=0.0,
                    confidence=1.0,
                    risk_score=0.0,
                    explanation="All systems nominal"
                )
        return context
    
    async def execute_async(self, context: ActionContext, **kwargs) -> ActionContext:
        final_detection = getattr(context, '_final_detection', None)
        risk = getattr(context, '_risk', RiskScore(value=0.0, confidence=0.0))
        
        if self.core.policy:
            if hasattr(self.core.policy, 'decide') and asyncio.iscoroutinefunction(self.core.policy.decide):
                context._decision = await self.core.policy.decide(context, final_detection, risk)
            else:
                context._decision = self.core.policy.decide(context, final_detection, risk)
        else:
            if final_detection and final_detection.score > 0.3:
                context._decision = Decision(
                    action="pause",
                    reason=final_detection.reason,
                    severity=final_detection.score,
                    confidence=final_detection.confidence,
                    risk_score=risk.value,
                    explanation=f"Anomaly detected by {final_detection.source}"
                )
            else:
                context._decision = Decision(
                    action="continue",
                    reason="No anomalies detected",
                    severity=0.0,
                    confidence=1.0,
                    risk_score=0.0,
                    explanation="All systems nominal"
                )
        return context


class MemoryStep(PipelineStep):
    def __init__(self, core: AdaptiveFeedbackLoopCore):
        self.core = core
    
    def execute(self, context: ActionContext, **kwargs) -> ActionContext:
        decision = getattr(context, '_decision', None)
        final_detection = getattr(context, '_final_detection', None)
        risk = getattr(context, '_risk', RiskScore(value=0.0, confidence=0.0))
        
        if self.core.memory and decision:
            self.core.memory.store(context, final_detection, decision, risk)
        return context


class ExplainerStep(PipelineStep):
    def __init__(self, core: AdaptiveFeedbackLoopCore):
        self.core = core
    
    def execute(self, context: ActionContext, **kwargs) -> ActionContext:
        decision = getattr(context, '_decision', None)
        final_detection = getattr(context, '_final_detection', None)
        risk = getattr(context, '_risk', RiskScore(value=0.0, confidence=0.0))
        
        if self.core.explainer and decision:
            explanation = self.core.explainer.explain(context, final_detection, decision, risk)
            decision.explanation = explanation
        return context


class Pipeline:
    def __init__(self, core: AdaptiveFeedbackLoopCore):
        self.core = core
        self.steps: List[PipelineStep] = []
        self.event_bus = core.event_bus
        self._build_default_pipeline()
    
    def _build_default_pipeline(self):
        self.add_step(SensorStep(self.core))
        self.add_step(DetectorStep(self.core))
        self.add_step(CorrelatorStep(self.core))
        self.add_step(RiskStep(self.core))
        self.add_step(PolicyStep(self.core))
        self.add_step(MemoryStep(self.core))
        self.add_step(ExplainerStep(self.core))
    
    def add_step(self, step: PipelineStep) -> 'Pipeline':
        self.steps.append(step)
        return self
    
    def execute(self, context: ActionContext) -> ActionContext:
        self.event_bus.publish(Event("pipeline_started", {"context": context}))
        for step in self.steps:
            try:
                context = step.execute(context)
            except Exception as e:
                logger.error(f"Pipeline step error: {e}")
                raise PipelineError(f"Step {step.__class__.__name__} failed: {e}") from e
        self.event_bus.publish(Event("pipeline_finished", {"context": context}))
        return context
    
    async def execute_async(self, context: ActionContext) -> ActionContext:
        await self.event_bus.publish_async(Event("pipeline_started", {"context": context}))
        for step in self.steps:
            try:
                if hasattr(step, 'execute_async') and asyncio.iscoroutinefunction(step.execute_async):
                    context = await step.execute_async(context)
                else:
                    context = step.execute(context)
            except Exception as e:
                logger.error(f"Async pipeline step error: {e}")
                raise PipelineError(f"Step {step.__class__.__name__} failed: {e}") from e
        await self.event_bus.publish_async(Event("pipeline_finished", {"context": context}))
        return context
