## Context

json.loads/object lookup/UUID SQL parameter сейчас допускают исключения от sender-controlled hints. Native Dramatiq restart закрывает consumer sessions, освобождая locks уже исполняемых задач. Review статический; regression ещё не выполнена.

## Goals / Non-Goals

Сохранить sessions и processing locks при недействительном hint. Не подавлять настоящие DB failures, не доверять actor/args из notification, не обещать защиту от легитимного scan flooding.

## Decisions

Валидация в единственной границе Consumer.__next__: JSON object; scan только boolean true; иначе string UUID через stdlib UUID. Невалидные hints пропускаются, DB consume_one остаётся вне parser exception handler. UUID приводится к стандартной строке, чтобы альтернативное валидное представление не обходило in_processing. Нет логирования payload.

## Risks / Trade-offs

Неаутентифицированный database sender всё ещё может будить consumer; queue/data access ограничивает PostgreSQL. Сохраняются at-least-once и обычные connection-error semantics.

Независимое review выявило, что canonical hint при alternate durable UUID оставляет ACK lock. Поэтому message_lock и in_processing SHALL использовать одинаковое canonical UUID представление; durable message_id сохраняется. Стандартные Dramatiq UUID lock keys не меняются. Для custom alternate UUID не смешивать старые/новые workers при rolling restart.
