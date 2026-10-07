## ADDED Requirements

### Requirement: Malformed notification tolerance

Consumer SHALL пропускать недействительные JSON/object/message_id hints без исключения, закрытия sessions или освобождения locks исполняемых задач. Только boolean true scan marker SHALL запускать queue scan. ID-only и legacy full hints с действительным UUID MUST сохраняться; durable claim остаётся authoritative.

#### Scenario: Restricted sender malformed hints
- **WHEN** роль без queue privileges отправляет malformed JSON, scalar/array/null, missing ID или invalid UUID на известный enqueue channel
- **THEN** consumer сохраняет sessions и processing locks и claims следующую действительную задачу

#### Scenario: Legacy and scan control
- **WHEN** consumer получает valid UUID legacy hint либо boolean true scan marker
- **THEN** выполняется обычный durable claim либо queue scan, без доверия к sender actor/args
