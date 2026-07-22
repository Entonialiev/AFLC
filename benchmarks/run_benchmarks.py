#!/usr/bin/env python
"""
Утилита для запуска всех бенчмарков AFLC
"""

import subprocess
import sys
import os


def run_benchmarks():
    """Запускает все бенчмарки и выводит отчёт"""
    print("=" * 60)
    print("🚀 AFLC Benchmark Suite v0.8.0")
    print("=" * 60)
    print()
    
    # Проверяем установку pytest-benchmark
    try:
        import pytest_benchmark
    except ImportError:
        print("❌ pytest-benchmark не установлен.")
        print("   Установите: pip install pytest-benchmark")
        return 1
    
    # Запускаем бенчмарки
    cmd = [
        sys.executable,
        "-m",
        "pytest",
        "benchmarks/",
        "--benchmark-only",
        "--benchmark-json=benchmark_results.json"
    ]
    
    print("🔄 Запуск бенчмарков...")
    print()
    
    result = subprocess.run(cmd)
    
    if result.returncode == 0:
        print()
        print("=" * 60)
        print("✅ Бенчмарки успешно завершены!")
        print(f"   Результаты сохранены в: benchmark_results.json")
        print()
        print("📊 Для просмотра отчёта выполните:")
        print("   pytest benchmarks/ --benchmark-only --benchmark-histogram")
        print("=" * 60)
    else:
        print("❌ Ошибка при запуске бенчмарков")
    
    return result.returncode


if __name__ == "__main__":
    sys.exit(run_benchmarks())
