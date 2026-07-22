"""
StatisticalDetector — адаптивный детектор на основе EWMA
Версия: 1.0.0
"""

import numpy as np
from typing import Optional, Dict, List
from collections import deque
from dataclasses import dataclass, field

from ..core import ActionContext, Detection


@dataclass
class Baseline:
    """Базовая линия для одного эндпоинта"""
    mean: float = 0.0
    variance: float = 0.0
    std: float = 0.0
    alpha: float = 0.3  # Коэффициент сглаживания EWMA
    history: deque = field(default_factory=lambda: deque(maxlen=1000))
    n: int = 0
    is_initialized: bool = False
    
    def update(self, value: float):
        """Обновляет базовую линию с использованием EWMA"""
        self.history.append(value)
        self.n += 1
        
        if not self.is_initialized:
            self.mean = value
            self.variance = 0.0
            self.is_initialized = True
        else:
            # EWMA для среднего
            self.mean = self.alpha * value + (1 - self.alpha) * self.mean
            # EWMA для дисперсии
            delta = value - self.mean
            self.variance = (1 - self.alpha) * (self.variance + self.alpha * delta * delta)
            self.std = np.sqrt(max(self.variance, 1e-10))
    
    def z_score(self, value: float) -> float:
        """Вычисляет Z-score относительно текущей базовой линии"""
        if not self.is_initialized or self.std == 0:
            return 0.0
        return abs((value - self.mean) / self.std)
    
    @property
    def confidence(self) -> float:
        """Уверенность в базовой линии (зависит от количества данных)"""
        if self.n < 10:
            return 0.3
        if self.n < 50:
            return 0.6
        return min(1.0, 0.8 + self.n / 500)


class StatisticalDetector:
    """
    Адаптивный детектор на основе EWMA.
    Строит отдельную базовую линию для каждого эндпоинта.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """
        Args:
            config: словарь с настройками:
                {
                    "alpha": 0.3,  # Коэффициент сглаживания
                    "z_score_threshold": 3.0,  # Порог для аномалии
                    "min_samples": 10,  # Минимальное количество данных для детекции
                }
        """
        self.config = config or {}
        self.alpha = self.config.get("alpha", 0.3)
        self.z_score_threshold = self.config.get("z_score_threshold", 3.0)
        self.min_samples = self.config.get("min_samples", 10)
        self.name = "statistical_detector"
        
        # Базовые линии для каждого эндпоинта и метрики
        self.baselines: Dict[str, Dict[str, Baseline]] = {}
    
    def _get_baseline(self, endpoint: str, metric: str) -> Baseline:
        """Получает или создаёт базовую линию для эндпоинта и метрики"""
        if endpoint not in self.baselines:
            self.baselines[endpoint] = {}
        if metric not in self.baselines[endpoint]:
            self.baselines[endpoint][metric] = Baseline(alpha=self.alpha)
        return self.baselines[endpoint][metric]
    
    def _update_baselines(self, context: ActionContext):
        """Обновляет все базовые линии на основе текущего контекста"""
        endpoint = context.endpoint
        
        # Время ответа
        baseline = self._get_baseline(endpoint, "latency")
        baseline.update(context.latency_ms)
        
        # Размер ответа
        baseline = self._get_baseline(endpoint, "size")
        baseline.update(context.response_size)
        
        # Код ошибки (0 = success, другие = error)
        error_value = 0.0 if context.error_code == 0 else 1.0
        baseline = self._get_baseline(endpoint, "error")
        baseline.update(error_value)
    
    def detect(self, context: ActionContext) -> Optional[Detection]:
        """
        Анализирует контекст и возвращает Detection при обнаружении аномалии
        """
        # Обновляем базовые линии
        self._update_baselines(context)
        
        endpoint = context.endpoint
        
        # Проверяем каждую метрику
        anomalies = []
        
        for metric_name, value in [
            ("latency", context.latency_ms),
            ("size", context.response_size),
            ("error", 0.0 if context.error_code == 0 else 1.0)
        ]:
            baseline = self._get_baseline(endpoint, metric_name)
            
            # Пропускаем, если недостаточно данных
            if baseline.n < self.min_samples:
                continue
            
            z = baseline.z_score(value)
            
            if z > self.z_score_threshold:
                anomalies.append({
                    "metric": metric_name,
                    "value": value,
                    "z_score": z,
                    "mean": baseline.mean,
                    "std": baseline.std,
                    "confidence": baseline.confidence
                })
        
        if not anomalies:
            return None
        
        # Выбираем самую сильную аномалию
        best = max(anomalies, key=lambda x: x["z_score"])
        
        # Нормализуем score от z-score к 0-1
        score = min(1.0, (best["z_score"] - self.z_score_threshold) / 5.0)
        confidence = best["confidence"]
        
        return Detection(
            source=self.name,
            score=score,
            confidence=confidence,
            reason=f"Adaptive anomaly: {best['metric']} = {best['value']:.1f} (baseline: {best['mean']:.1f} ± {best['std']:.1f}, z={best['z_score']:.1f})",
            tags=["adaptive", "statistical", best["metric"]],
            metadata={
                "metric": best["metric"],
                "z_score": best["z_score"],
                "baseline_mean": best["mean"],
                "baseline_std": best["std"],
                "samples": baseline.n
            }
        )
    
    def get_statistics(self, endpoint: str) -> Dict[str, Dict[str, float]]:
        """
        Возвращает текущую статистику для эндпоинта
        """
        result = {}
        if endpoint not in self.baselines:
            return result
        
        for metric, baseline in self.baselines[endpoint].items():
            if baseline.is_initialized:
                result[metric] = {
                    "mean": baseline.mean,
                    "std": baseline.std,
                    "n": baseline.n,
                    "confidence": baseline.confidence
                }
        return result


# --- ПРИМЕР ИСПОЛЬЗОВАНИЯ ---
if __name__ == "__main__":
    print("🧪 StatisticalDetector Test")
    print("=" * 50)
    
    detector = StatisticalDetector(config={"z_score_threshold": 2.5})
    
    # Создаём нормальные данные для обучения
    print("\n📊 Обучение на нормальных данных...")
    for i in range(50):
        context = ActionContext(
            action_id=f"train-{i}",
            endpoint="/api/test",
            method="GET",
            latency_ms=100 + np.random.normal(0, 10),
            response_size=1024 + np.random.normal(0, 50),
            error_code=0
        )
        detector.detect(context)
    
    # Проверяем нормальный запрос
    normal_context = ActionContext(
        action_id="test-normal",
        endpoint="/api/test",
        method="GET",
        latency_ms=105,
        response_size=1000,
        error_code=0
    )
    
    result = detector.detect(normal_context)
    print(f"\n🟢 Нормальный запрос: {'No anomaly' if result is None else result.score}")
    
    # Проверяем аномальный запрос
    anomaly_context = ActionContext(
        action_id="test-anomaly",
        endpoint="/api/test",
        method="GET",
        latency_ms=350,  # 3+ std от нормы
        response_size=1024,
        error_code=0
    )
    
    result = detector.detect(anomaly_context)
    print(f"\n🔴 Аномальный запрос (latency=350ms):")
    if result:
        print(f"  Score: {result.score:.2f}")
        print(f"  Confidence: {result.confidence:.2f}")
        print(f"  Reason: {result.reason}")
    
    # Показываем статистику
    print(f"\n📊 Статистика для /api/test:")
    stats = detector.get_statistics("/api/test")
    for metric, values in stats.items():
        print(f"  {metric}: mean={values['mean']:.1f}, std={values['std']:.1f}, n={values['n']}")
