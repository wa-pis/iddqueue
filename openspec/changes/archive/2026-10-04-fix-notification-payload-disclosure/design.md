## Context

См. proposal.md. ENQUEUE/ACK/NACK содержат одинаковый CASE: message::text для <8000 bytes, ID для больших. Consumer уже refetches authoritative SQL rows; results, retry/unlock/control/cancellation используют минимальные hints. PostgreSQL channels не имеют ACL на originating table.

## Goals / Non-Goals

**Goals:** убрать данные задачи из всех исходящих task hints; доказать permissions boundary и сохранить lifecycle.

**Non-Goals:** тайные каналы, новый authentication layer, exactly-once, сокрытие UUID/времени активности от ролей той же БД, исправление других advisory.

## Decisions

Заменить три CASE на существующий jsonb_build_object('message_id', %s::text)::text. Не вводить helper/новую зависимость или флаг: полный payload не нужен consumer и небезопасен. Не менять legacy input parser в этом fix. Проследить transactional/batch/dedup/scheduler publication через общие SQL sinks; остальные pg_notify calls проверить на отсутствие task content.

Functional regression создаёт случайную restricted NOLOGIN role и использует SET ROLE на отдельной listener connection: CONNECT allowed, USAGE/SELECT отсутствуют, чтение таблицы реально даёт InsufficientPrivilege. Listener слушает известный quoted channel; проверяются enqueue, ACK, NACK, small/large и schema/prefix. Фикстура и роль удаляются с отдельной privileged connection после закрытия sessions. Только выделенный PostgreSQL; не production role.

## Risks / Trade-offs

- Старые producers/worker ACK раскрывают данные → остановить/обновить всех участников; rolling mixed deployment не считать remediation.
- Downstream custom LISTEN client ждёт full JSON → описать смену wire payload; UUID hint + authorized SQL fetch.
- NOTIFY metadata (UUID/timing) остаётся видимым → не обещать tenant confidentiality для всей shared DB.
- Roles могут зависеть от PUBLIC grants → regression явно подтвердить реальный запрет schema/table до проверки уведомлений.

## Migration Plan

DDL не требуется; backup как обычно, stop/update/restart всех producers/workers/schedulers. Legacy hints принимаются, однако старые publishers нельзя оставлять активными. Rollback вернёт disclosure; не объявлять его безопасным. Обновить известное ограничение migration.md только после passing regression.
