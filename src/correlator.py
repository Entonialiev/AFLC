"""
Correlator — объединяет результаты детекторов в единый Detection
Версия: 1.0.0
"""

from typing import List, Optional, Dict
from collections import Counter
import numpy as np

from .core import Detection


class Correlator:
    """
    Объединяет результаты всех детекторов в единый Detection.
    
    Стратегии:
    - weighted: взвешенное среднее с учётом confidence
    - max: максимальный score
    - voting: голосование (если несколько детекторов согласны)
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """
        Args:
            config: словарь с настройками:
                {
                    "strategy": "weighted",  # или "max", "voting"
                    "detector_weights": {"rule": 1.2, "statistical": 1.0},
                    "threshold": 0.3,  # минимальный score для детекции
                }
        """
        self.config = config or {}
        self.strategy = self.config.get("strategy", "weighted")
        self.threshold = self.config.get("threshold", 0.3)
        
        # Веса для детекторов (можно переопределить)
        self.detector_weights = self.config.get("detector_weights", {
            "rule_detector": 1.2,
            "statistical_detector": 1.0,
            "isolation_forest": 1.1,
            "ml_detector": 0.8,
        })
    
    def correlate(self, detections: List[Detection]) -> Optional[Detection]:
        """
        Объединяет список Detection в один.
        
        Returns:
            Detection или None, если нет аномалий
        """
        if not detections:
            return None
        
        # Фильтруем по порогу
        filtered = [d for d in detections if d.score >= self.threshold]
        if not filtered:
            return None
        
        # Выбираем стратегию
        if self.strategy == "max":
            return self._correlate_max(filtered)
        elif self.strategy == "voting":
            return self._correlate_voting(filtered)
        else:  # weighted
            return self._correlate_weighted(filtered)
    
    def _correlate_max(self, detections: List[Detection]) -> Detection:
        """Берёт детекцию с максимальным score"""
        return max(detections, key=lambda x: x.score)
    
    def _correlate_weighted(self, detections: List[Detection]) -> Detection:
        """
        Вычисляет взвешенное среднее с учётом confidence
        и весов детекторов.
        """
        total_weight = 0.0
        weighted_score = 0.0
        weighted_confidence = 0.0
        
        # Собираем все теги
        all_tags = []
        all_metadata = {}
        
        for detection in detections:
            weight = self.detector_weights.get(detection.source, 1.0)
            # Умножаем на confidence
            effective_weight = weight * detection.confidence
            total_weight += effective_weight
            weighted_score += detection.score * effective_weight
            weighted_confidence += detection.confidence * effective_weight
            
            all_tags.extend(detection.tags)
            all_metadata[detection.source] = detection.metadata
        
        if total_weight == 0:
            return detections[0]
        
        final_score = weighted_score / total_weight
        final_confidence = min(1.0, weighted_confidence / total_weight)
        
        # Выбираем лучший reason и tags
        best_detection = max(detections, key=lambda x: x.score)
        
        # Находим самый частый тег
        tag_counter = Counter(all_tags)
        most_common_tags = [tag for tag, _ in tag_counter.most_common(3)]
        
        return Detection(
            source="correlator",
            score=final_score,
            confidence=final_confidence,
            reason=f"Combined from {len(detections)} detectors: {best_detection.reason}",
            tags=list(set(most_common_tags + ["correlated"])),
            metadata={
                "sources": [d.source for d in detections],
                "original_scores": {d.source: d.score for d in detections},
                "original_confidences": {d.source: d.confidence for d in detections},
                **all_metadata
            }
        )
    
    def _correlate_voting(self, detections: List[Detection]) -> Optional[Detection]:
        """
        Голосование: если несколько детекторов согласны.
        Простая версия: берём среднее от всех.
        """
        # В этой версии просто усредняем
        avg_score = np.mean([d.score for d in detections])
        avg_confidence = np.mean([d.confidence for d in detections])
        
        best_detection = max(detections, key=lambda x: x.score)
        
        return Detection(
            source="correlator",
            score=float(avg_score),
            confidence=float(avg_confidence),
            reason=f"Voting from {len(detections)} detectors: {best_detection.reason}",
            tags=["voting", "correlated"],
            metadata={
                "sources": [d.source for d in detections],
                "original_scores": {d.source: d.score for d in detections}
            }
        )


# --- ПРИМЕР ИСПОЛЬЗОВАНИЯ ---
if __name__ == "__main__":
    print("🔗 Correlator Test")
    print("=" * 40)
    
    # Создаём тестовые детекции
    from .core import Detection
    
    detections = [
        Detection(
            source="rule_detector",
            score=0.7,
            confidence=0.9,
            reason="Timeout > 2000ms",
            tags=["timeout"]
        ),
        Detection(
            source="statistical_detector",
            score=0.8,
            confidence=0.6,
            reason="Z-score 4.5σ",
            tags=["statistical"]
        )
    ]
    
    correlator = Correlator()
    result = correlator.correlate(detections)
    
    print(f"✅ Скоррелировано: {result.source}")
    print(f"  Score: {result.score:.2f}")
    print(f"  Confidence: {result.confidence:.2f}")
    print(f"  Reason: {result.reason}")
    print(f"  Tags: {result.tags}")
