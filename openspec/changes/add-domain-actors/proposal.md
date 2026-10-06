## Why

Пользователь авторизовал Domain API: queue_name задаётся один раз доменом, tasks импортируются без DSN, broker передаётся при startup.

## What Changes

Domain(name).actor создаёт стандартные Dramatiq Actors с domain queue и qualified names. register(broker) явно привязывает domain actors к заданному broker, проверяя options. Отправка до регистрации запрещена. Один framework-independent bootstrap/example; стандартный CLI и Docker application example.

## Capabilities

### New Capabilities
- `domain-actors`: domain declarations и явная late binding.

## Impact

Additive API; существующие PostgresBroker/Actors совместимы. RC2 не перепубликуется. Новых зависимостей нет. FastAPI не требуется.
