## Why

Импорт actor связывает его с текущим глобальным broker Dramatiq. Для PostgreSQL приложений это требует ранней настройки и усложняет импорты, FastAPI lifespan и тестовую изоляцию. Пользователь просит исследование и план, не реализацию нового API.

## What Changes

Зафиксировать поведение Dramatiq 2.2.1 и IDDQueue, сравнить native bootstrap/factory, позднюю explicit binding и deferred declarations. Определить минимальное решение для стабильных импортируемых actors с .send(), без fallback RabbitMQ/Redis. После исследования согласовать API и подготовить отдельный implementation change.

Основной сценарий независим от framework: tasks разложены по доменным областям, импортируются без знания DSN; приложение передаёт DSN при startup в одной точке входа. Эта точка собирает домены и запускается стандартным Dramatiq CLI, в том числе в Docker. Исследовать как общую очередь/broker, так и раздельные очереди доменов, без обязательного FastAPI.

## Capabilities

Исследовательский change: runtime/spec behavior не меняется; delta specs будут нужны для согласованной реализации.

## Impact

Только planning artifacts/roadmap. Никаких новых runtime decorators/registry/dependencies, релизов или изменений RC2 в этом этапе.
