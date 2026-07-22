"""
AFLC Configuration — загрузка настроек из YAML
Версия: 1.0.0
"""

import os
import yaml
from typing import Dict, Any, Optional
from dataclasses import dataclass, field


@dataclass
class DetectorConfig:
    """Конфигурация детектора"""
    name: str
    enabled: bool = True
    params: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AFLCConfig:
    """Полная конфигурация AFLC"""
    agent_id: str = "default-agent"
    window_size: int = 30
    severity_threshold: float = 0.3
    
    detectors: Dict[str, DetectorConfig] = field(default_factory=dict)
    
    correlator: Dict[str, Any] = field(default_factory=dict)
    risk: Dict[str, Any] = field(default_factory=dict)
    policy: Dict[str, Any] = field(default_factory=dict)
    memory: Dict[str, Any] = field(default_factory=dict)


def load_config(config_path: str) -> AFLCConfig:
    """
    Загружает конфигурацию из YAML-файла.
    
    Args:
        config_path: путь к файлу config.yaml
        
    Returns:
        AFLCConfig: объект конфигурации
    """
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Config file not found: {config_path}")
    
    with open(config_path, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)
    
    return _parse_config(data)


def _parse_config(data: Dict[str, Any]) -> AFLCConfig:
    """Парсит YAML-данные в объект конфигурации"""
    config = AFLCConfig(
        agent_id=data.get("agent_id", "default-agent"),
        window_size=data.get("window_size", 30),
        severity_threshold=data.get("severity_threshold", 0.3)
    )
    
    # Парсим детекторы
    for name, params in data.get("detectors", {}).items():
        if isinstance(params, bool):
            config.detectors[name] = DetectorConfig(name=name, enabled=params)
        elif isinstance(params, dict):
            config.detectors[name] = DetectorConfig(
                name=name,
                enabled=params.get("enabled", True),
                params=params.get("params", {})
            )
    
    config.correlator = data.get("correlator", {})
    config.risk = data.get("risk", {})
    config.policy = data.get("policy", {})
    config.memory = data.get("memory", {})
    
    return config


def save_config(config: AFLCConfig, config_path: str) -> None:
    """Сохраняет конфигурацию в YAML-файл"""
    data = {
        "agent_id": config.agent_id,
        "window_size": config.window_size,
        "severity_threshold": config.severity_threshold,
        "detectors": {
            name: {
                "enabled": d.enabled,
                "params": d.params
            } for name, d in config.detectors.items()
        },
        "correlator": config.correlator,
        "risk": config.risk,
        "policy": config.policy,
        "memory": config.memory
    }
    
    with open(config_path, 'w', encoding='utf-8') as f:
        yaml.dump(data, f, default_flow_style=False, allow_unicode=True)
