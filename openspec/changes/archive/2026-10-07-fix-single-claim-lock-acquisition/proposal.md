## Why

RC4 candidate CI37555454492(Python3.14/PostgreSQL18) выявил lock-release failures. На dedicatedPG18.6 forced Seq Scan воспроизвёл50лишних reentrant advisory lock acquisitions после ACK: volatile WHERE function выполняется до message_id filter для каждой строки.

## What Changes

- Uncorrelated scalar SQL subquery вычисляет advisory lock один раз на claim statement независимо от scan plan.
- Regression forced Seq Scan на фоне других queued rows проверяет ACK/NACK lock release и следующий claim.
- Отменить readiness прежнего candidate a529e5e, пересобрать ещё не опубликованный RC4 и провести новый полный gate/CI.

## Capabilities

### New Capabilities
Нет.

### Modified Capabilities
Нет: исправление existing Prompt completed lock release/authoritative claim; skip_specs: true.

## Impact

Одна строка CONSUME_ONE SQL, functional tests и release evidence. Без schema/API/dependency изменений.
