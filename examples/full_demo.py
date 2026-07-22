C:\Users\Comp>C:\Users\Comp\Downloads\AFLC-main\AFLC-main\examples\full_demo.py
============================================================
🔁 AFLC Full Demo
============================================================

📦 1. Инициализация AFLC...
✅ AFLC создан

📡 2. Подписка на события...
✅ Подписки созданы

🚀 3. Отправка действия...
   📨 Событие: ExecutionCreated (id=c1e7b74d-7323-46c2-8de5-9f1ce782355d)
   Execution ID: c1e7b74d-7323-46c2-8de5-9f1ce782355d
   Status: created

🔄 4. Перевод в состояние PENDING...
   Status: pending

🔄 5. Перевод в состояние RUNNING...
   📨 Событие: ExecutionCreated (id=d7bade45-4217-4d7a-9896-9cece43a4fe0)
   📨 Событие: ExecutionStarted (id=c1e7b74d-7323-46c2-8de5-9f1ce782355d)
   Status: pending

📊 6. Добавление наблюдений...
   📨 Событие: ExecutionCreated (id=4c4c47d5-5851-4940-9d6c-f599fb3ca839)
   📨 Событие: ObservationRecorded (metric=latency_ms, value=150.0)
   ✅ Добавлено наблюдение: latency_ms=150ms
   📨 Событие: ExecutionCreated (id=82f871e0-9fe2-4bef-a120-7608f13a15a3)
   📨 Событие: ObservationRecorded (metric=response_size, value=2048)
   ✅ Добавлено наблюдение: response_size=2048b

🔍 7. Добавление находок...
   📨 Событие: ExecutionCreated (id=3ad9b2c9-9abf-4c97-b884-ed01a7715553)
   📨 Событие: FindingCreated (source=rule, score=0.7)
   ✅ Находка: High latency detected (score=0.7)
   📨 Событие: ExecutionCreated (id=3a5439a5-5819-47bc-af9b-1d2f1e8e1e0c)
   📨 Событие: FindingCreated (source=statistical, score=0.8)
   ✅ Находка: Response size anomaly (score=0.8)

⚙️ 8. Завершение обработки...
   📨 Событие: ExecutionCreated (id=9a48c44f-d572-4d04-a211-8addedbd75bf)
   Status: pending

📈 9. Оценка риска...
   📨 Событие: ExecutionCreated (id=d448137b-931b-4103-9ae4-e1ff080cd1e2)
   📨 Событие: RiskEvaluated (score=0.85, components={'rule': 0.7, 'statistical': 0.8, 'endpoint': 0.9})
   ✅ Оценка риска: 0.85

⚖️ 10. Принятие решения...
   📨 Событие: ExecutionCreated (id=8450dfd4-5850-44af-8bc7-8358d5e76a6b)
   📨 Событие: DecisionMade (action=block)
   ✅ Решение: BLOCK

📝 11. Генерация объяснения...
   📨 Событие: ExecutionCreated (id=a7e48a19-ab38-4830-b707-7185f2091b20)
   📨 Событие: ExplanationGenerated (text=Action blocked due to high risk score (0.85). Dete...)
   ✅ Объяснение добавлено

📦 12. Архивация...
   📨 Событие: ExecutionCreated (id=24a82978-b7a2-4a0e-81e0-5131272cf8b5)
   📨 Событие: ExecutionArchived (id=c1e7b74d-7323-46c2-8de5-9f1ce782355d)
   ✅ Статус: pending

📋 13. Получение Execution из репозитория...
   Execution ID: c1e7b74d-7323-46c2-8de5-9f1ce782355d
   Status: archived
   Risk: 0.85
   Decision: block

📊 14. Статистика...
   Всего Execution: 3
   - created: 2
   - archived: 1

============================================================
✅ Демонстрация завершена!
   Все компоненты работают корректно
============================================================

C:\Users\Comp>
