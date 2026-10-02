# postgres-task-deduplication Specification

## Purpose

Предотвратить повторную публикацию одной логической задачи конкурентными producers в выбранной области хранения.

## Requirements

### Requirement: Idempotent publishing

Отправка с deduplication key SHALL создавать не более одного сообщения в пределах schema/prefix/логической очереди до истечения явно заданного TTL; повтор SHALL возвращать исходный message_id без перезаписи payload.

#### Scenario: Concurrent producers
- **WHEN** два producers одновременно отправляют разные UUID с одним ключом
- **THEN** оба получают один message_id и в очереди присутствует одна задача

#### Scenario: Transaction rollback
- **WHEN** отправка с ключом откатывается во внешней транзакции
- **THEN** ключ и задача отсутствуют; следующий producer может опубликовать задачу

#### Scenario: Expired key
- **WHEN** TTL ключа истёк
- **THEN** повторная отправка может создать новую задачу

#### Scenario: Storage isolation
- **WHEN** одинаковый ключ используется в разных schema/prefix
- **THEN** каждая область получает независимую задачу
