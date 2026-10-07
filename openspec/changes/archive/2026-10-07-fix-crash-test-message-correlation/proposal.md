## Why

Finalcandidate6eb5aac CI37556241736initial5/6: старый test_crash(Python3.10/PG18) получил ACK и не вызвал Timeout. Тест не связывает ACK с задачей и не гарантирует, что1.5s actor ещё выполняется при SIGKILL; source-backed outcome неоднозначен.

## What Changes

- Управляемый crash actor сообщает started и ждёт durable ready marker, вместо временного сна.
- Проверить ResultTimeout конкретного сообщения после SIGKILL и его result после restart.
- ACK listener optional message ID filtering; massive/nack/reconnect tests получают только свои ACK.

## Capabilities

### New Capabilities
Нет.

### Modified Capabilities
Нет: test determinism существующего at-least-once/recovery контракта, skip_specs: true.

## Impact

Только tests/func, без production API/dependencies/schema изменений. Новый localgate/signedcommit/actualCI перед RC4tag.
