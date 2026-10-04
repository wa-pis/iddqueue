## ADDED Requirements

### Requirement: Minimal outgoing task notifications

Broker SHALL отправлять в уведомлениях публикации, ACK и NACK только JSON object с message_id, независимо от размера задачи. Аргументы, options, actor names и failure diagnostics MUST оставаться в защищённом SQL storage и не попадать в notification payload. Приём legacy full hints SHALL сохраняться согласно Authoritative queue claim.

#### Scenario: Unprivileged listener
- **WHEN** отдельная роль с CONNECT без USAGE схемы и SELECT очереди слушает известный канал при enqueue/ACK/NACK
- **THEN** её чтение таблицы запрещено, а каждое полученное уведомление содержит только message_id и не раскрывает task data

#### Scenario: Different message sizes and namespaces
- **WHEN** публикуются малые и большие сообщения в default и custom schema/prefix областях
- **THEN** уведомления всегда ID-only, consumer читает актуальную задачу из SQL, results и retry сохраняют поведение

#### Scenario: Legacy notification reception
- **WHEN** consumer получает старое полное уведомление с устаревшими аргументами
- **THEN** consumer исполняет authoritative сохранённые данные и новое ACK/NACK содержит только ID
