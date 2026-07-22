"""
AFLC Exceptions
Version: 1.0.0
"""


class AFLCError(Exception):
    """Базовое исключение для всех ошибок AFLC"""
    pass


class DetectorError(AFLCError):
    """Ошибка в работе детектора"""
    pass


class PipelineError(AFLCError):
    """Ошибка в работе пайплайна"""
    pass


class PluginError(AFLCError):
    """Ошибка регистрации или работы плагина"""
    pass


class PolicyError(AFLCError):
    """Ошибка в работе политики"""
    pass


class MemoryError(AFLCError):
    """Ошибка в работе памяти"""
    pass


class ConfigurationError(AFLCError):
    """Ошибка конфигурации"""
    pass


class TimeoutError(AFLCError):
    """Таймаут выполнения"""
    pass
