"""
History Backend Benchmark
"""

import pytest
from src.history import MemoryHistory, SQLiteHistory


def generate_record(num: int = 0):
    """Генерирует тестовую запись"""
    return {
        "action_id": f"bench_{num}",
        "timestamp": 1234567.0 + num,
        "endpoint": "/api/test",
        "method": "GET",
        "latency_ms": 100.0 + num,
        "error_code": 0,
        "decision": "continue" if num % 2 == 0 else "pause",
        "severity": 0.0,
        "risk_score": 0.0,
        "metadata": {"test": True}
    }


def test_memory_history_add(benchmark):
    """Измеряет скорость добавления в MemoryHistory"""
    history = MemoryHistory({"max_size": 10000})
    record = generate_record()
    
    benchmark(history.add, record)


def test_memory_history_add_batch(benchmark):
    """Измеряет скорость добавления 100 записей в MemoryHistory"""
    history = MemoryHistory({"max_size": 10000})
    records = [generate_record(i) for i in range(100)]
    
    def add_batch():
        for r in records:
            history.add(r)
    
    benchmark(add_batch)


def test_memory_history_read_recent(benchmark):
    """Измеряет скорость чтения последних записей"""
    history = MemoryHistory({"max_size": 10000})
    for i in range(1000):
        history.add(generate_record(i))
    
    result = benchmark(history.get_recent, 10)
    assert len(result) == 10


def test_memory_history_read_recent_large(benchmark):
    """Измеряет скорость чтения из большой истории"""
    history = MemoryHistory({"max_size": 100000})
    for i in range(50000):
        history.add(generate_record(i))
    
    result = benchmark(history.get_recent, 100)
    assert len(result) == 100


def test_sqlite_history_add(benchmark, temp_db_path):
    """Измеряет скорость добавления в SQLiteHistory"""
    history = SQLiteHistory({"db_path": temp_db_path, "max_records": 100000})
    record = generate_record()
    
    benchmark(history.add, record)


def test_sqlite_history_add_batch(benchmark, temp_db_path):
    """Измеряет скорость добавления 100 записей в SQLiteHistory"""
    history = SQLiteHistory({"db_path": temp_db_path, "max_records": 100000})
    records = [generate_record(i) for i in range(100)]
    
    def add_batch():
        for r in records:
            history.add(r)
    
    benchmark(add_batch)


def test_sqlite_history_read_recent(benchmark, temp_db_path):
    """Измеряет скорость чтения из SQLiteHistory"""
    history = SQLiteHistory({"db_path": temp_db_path, "max_records": 100000})
    for i in range(1000):
        history.add(generate_record(i))
    
    result = benchmark(history.get_recent, 10)
    assert len(result) == 10


def test_history_clear(benchmark):
    """Измеряет скорость очистки истории"""
    history = MemoryHistory({"max_size": 10000})
    for i in range(1000):
        history.add(generate_record(i))
    
    benchmark(history.clear)


def test_memory_history_stats(benchmark):
    """Измеряет скорость получения статистики"""
    history = MemoryHistory({"max_size": 10000})
    for i in range(1000):
        history.add(generate_record(i))
    
    result = benchmark(history.get_stats)
    assert result["total"] == 1000
