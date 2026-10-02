## Context

SQL экземпляров уже разделён схемой/префиксом, но каналы уведомлений и ключи advisory locks сейчас зависят от очереди или message_id без области хранения. Нужна последовательная изоляция приложений в общей PostgreSQL-базе. Текущая база — Psycopg 3 и Dramatiq 2.2.1; локальная миграция уже проверена. См. proposal.md и delta spec.

## Goals / Non-Goals

**Goals:** Изоляция приложений и результатов, проверенная на реальном PostgreSQL.

**Non-Goals:** замена стандартного worker Dramatiq, exactly-once, автоматическая публикация релиза.

## Decisions

Изоляция определяется парой schema/prefix; результат по-прежнему связывается с UUID сообщения. Для нестандартных областей добавить стабильный digest области в NOTIFY channels и вход SHA256 advisory lock. Сохранять длину каналов в пределах PostgreSQL identifier limit, покрыть цитирование и коллизии очевидных комбинаций тестами. Стандартные каналы можно сохранить для default-области, чтобы не менять её без необходимости. use_namespace_prefix_keys=True отклонять явно: таблица не является key-value storage со строковыми ключами. Двухпроцессная проверка должна включать большие payload, когда потребитель делает fetch_by_id.

## Risks / Trade-offs

Одинаковые старые и новые конфигурации нестандартных областей имеют разные каналы/locks: требуется согласованная остановка и обновление workers. Для строгой изоляции одних разных queue_name недостаточно.

## Migration Plan

Выполнить tasks.md, повторить релевантные интеграционные проверки и сборку. Для изменения SQL подготовить явную миграцию существующей базы и обратимый путь до включения новой функции. Новые опциональные возможности включаются явно. После проверки синхронизировать delta spec и архивировать change.

## Implementation Notes

Общий storage_namespace сохраняет разделители NUL между PostgreSQL schema/prefix;
NUL в SQL identifiers невозможен, поэтому пары не склеиваются неоднозначно.
QueryManager.channel вычисляет имя по текущим schema/prefix. Default-короткие
каналы сохранены, остальные — dpg. плюс digest длиной 48 hex символов.

ENQUEUE и STORE используют параметризованное имя канала, ACK/NACK/LISTEN —
тот же helper. Consume/unlock и CLI retry включают namespace в lock input;
default lock input сохраняется. Coordination переиспользует общий namespace,
сохраняя прежнее вычисление собственных locks/channels. SQL metrics уже scoped.

Results UUID API сохраняется. use_namespace_prefix_keys=True отвергается до
создания pool; namespace base-класса не трактуется как SQL isolation boundary.
Таблицы не изменены. Документирована остановка всех старых участников перед
обновлением non-default areas и default-очередей с длинными именами.
