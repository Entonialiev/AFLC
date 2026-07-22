"""
Memory — сохранение истории и самообучение
Версия: 1.0.0
"""

import json
import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from collections import deque
import os

from .core import ActionContext, Detection, Decision, RiskScore


@dataclass
class MemoryRecord:
    """Запись в памяти"""
    timestamp: float
    action_id: str
    endpoint: str
    method: str
    latency_ms: float
    error_code: int
    detection_score: float
    detection_confidence: float
    detection_source: str
    decision_action: str
    decision_reason: str
    risk_score: float
    feedback: Optional[str] = None  # "tp", "fp", "tn", "fn"
    feedback_timestamp: Optional[float] = None


class Memory:
    """
    Хранит историю решений и позволяет корректировать веса детекторов.
    """
    
    def __init__(self, max_size: int = 10000, storage_file: Optional[str] = None):
        self.max_size = max_size
        self.storage_file = storage_file
        self.records: deque = deque(maxlen=max_size)
        
        # Статистика по детекторам
        self.detector_stats: Dict[str, Dict[str, int]] = {}
        
        # Загружаем историю из файла, если есть
        if storage_file and os.path.exists(storage_file):
            self._load()
    
    def store(self, context: ActionContext, detection: Optional[Detection],
              decision: Decision, risk: RiskScore) -> None:
        """Сохраняет запись о решении"""
        record = MemoryRecord(
            timestamp=time.time(),
            action_id=context.action_id,
            endpoint=context.endpoint,
            method=context.method,
            latency_ms=context.latency_ms,
            error_code=context.error_code,
            detection_score=detection.score if detection else 0.0,
            detection_confidence=detection.confidence if detection else 0.0,
            detection_source=detection.source if detection else "none",
            decision_action=decision.action,
            decision_reason=decision.reason,
            risk_score=risk.value
        )
        self.records.append(record)
        
        # Сохраняем в файл
        if self.storage_file:
            self._save()
    
    def add_feedback(self, action_id: str, feedback: str) -> bool:
        """
        Добавляет обратную связь для конкретного действия.
        
        Args:
            action_id: ID действия
            feedback: "tp" (True Positive), "fp" (False Positive),
                      "tn" (True Negative), "fn" (False Negative)
        """
        for record in self.records:
            if record.action_id == action_id:
                record.feedback = feedback
                record.feedback_timestamp = time.time()
                self._update_stats(record.detection_source, feedback)
                if self.storage_file:
                    self._save()
                return True
        return False
    
    def _update_stats(self, source: str, feedback: str):
        """Обновляет статистику по детекторам"""
        if source not in self.detector_stats:
            self.detector_stats[source] = {"tp": 0, "fp": 0, "tn": 0, "fn": 0}
        
        if feedback in self.detector_stats[source]:
            self.detector_stats[source][feedback] += 1
    
    def get_detector_accuracy(self, source: str) -> float:
        """
        Возвращает точность детектора на основе обратной связи.
        """
        stats = self.detector_stats.get(source, {})
        tp = stats.get("tp", 0)
        fp = stats.get("fp", 0)
        tn = stats.get("tn", 0)
        fn = stats.get("fn", 0)
        
        total = tp + fp + tn + fn
        if total == 0:
            return 0.5  # нейтральная точность
        
        # (TP + TN) / (TP + FP + TN + FN)
        return (tp + tn) / total
    
    def get_detector_precision(self, source: str) -> float:
        """Возвращает precision детектора"""
        stats = self.detector_stats.get(source, {})
        tp = stats.get("tp", 0)
        fp = stats.get("fp", 0)
        
        if tp + fp == 0:
            return 0.5
        
        return tp / (tp + fp)
    
    def get_detector_recall(self, source: str) -> float:
        """Возвращает recall детектора"""
        stats = self.detector_stats.get(source, {})
        tp = stats.get("tp", 0)
        fn = stats.get("fn", 0)
        
        if tp + fn == 0:
            return 0.5
        
        return tp / (tp + fn)
    
    def get_recent_anomalies(self, limit: int = 10) -> List[MemoryRecord]:
        """Возвращает последние аномалии"""
        anomalies = []
        for record in self.records:
            if record.decision_action in ["pause", "block"]:
                anomalies.append(record)
                if len(anomalies) >= limit:
                    break
        return anomalies
    
    def get_stats(self) -> Dict[str, Any]:
        """Возвращает общую статистику памяти"""
        total = len(self.records)
        anomalies = sum(1 for r in self.records if r.decision_action in ["pause", "block"])
        
        return {
            "total_records": total,
            "anomalies": anomalies,
            "anomaly_rate": anomalies / total if total > 0 else 0.0,
            "detectors": list(self.detector_stats.keys()),
            "detector_stats": self.detector_stats
        }
    
    def _save(self):
        """Сохраняет память в файл"""
        if not self.storage_file:
            return
        
        data = {
            "records": [asdict(r) for r in self.records],
            "detector_stats": self.detector_stats
        }
        
        try:
            with open(self.storage_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"⚠️ Memory save error: {e}")
    
    def _load(self):
        """Загружает память из файла"""
        try:
            with open(self.storage_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Загружаем записи
            for record_data in data.get("records", []):
                self.records.append(MemoryRecord(**record_data))
            
            # Загружаем статистику
            self.detector_stats = data.get("detector_stats", {})
            
        except Exception as e:
            print(f"⚠️ Memory load error: {e}")
    
    def clear(self):
        """Очищает память"""
        self.records.clear()
        self.detector_stats.clear()
        if self.storage_file and os.path.exists(self.storage_file):
            os.remove(self.storage_file)
    
    def export_to_json(self, filepath: str) -> bool:
        """Экспортирует память в JSON-файл"""
        try:
            data = {
                "records": [asdict(r) for r in self.records],
                "detector_stats": self.detector_stats,
                "export_timestamp": time.time()
            }
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"⚠️ Export error: {e}")
            return False


# --- ПРИМЕР ИСПОЛЬЗОВАНИЯ ---
if __name__ == "__main__":
    print("🧠 Memory Test")
    print("=" * 40)
    
    memory = Memory(storage_file="memory_test.json")
    
    # Создаём тестовые данные
    context = ActionContext(
        action_id="test-001",
        endpoint="/api/test",
        method="GET",
        latency_ms=100,
        error_code=0
    )
    
    detection = Detection(
        source="rule_detector",
        score=0.8,
        confidence=0.9,
        reason="Timeout anomaly"
    )
    
    decision = Decision(
        action="pause",
        reason="Anomaly detected",
        severity=0.8,
        confidence=0.9,
        risk_score=0.7
    )
    
    risk = RiskScore(value=0.7, confidence=0.8, components={})
    
    # Сохраняем
    memory.store(context, detection, decision, risk)
    
    # Добавляем фидбек
    memory.add_feedback("test-001", "tp")
    
    # Смотрим статистику
    print("📊 Статистика:")
    stats = memory.get_stats()
    print(f"  Всего записей: {stats['total_records']}")
    print(f"  Аномалий: {stats['anomalies']}")
    
    print("\n📈 Точность детектора:")
    print(f"  Accuracy: {memory.get_detector_accuracy('rule_detector'):.2f}")
    print(f"  Precision: {memory.get_detector_precision('rule_detector'):.2f}")
    print(f"  Recall: {memory.get_detector_recall('rule_detector'):.2f}")
