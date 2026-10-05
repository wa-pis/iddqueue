## Context

Функциональные тесты импортируют actors из example и WorkerManager запускает этот модуль. Compose используется только пошаговой инструкцией; CI использует собственный PostgreSQL service. Семь .agents/skills файлов tracked, приложение агента читает локальные копии.

## Decisions

Оставить один test-only actors module с прежней конфигурацией и actor contracts, удалить main producer/pdb/debugger. Явные tests/func packages обеспечивают одинаковый import для pytest и отдельных Dramatiq процессов. Compose переносится без изменения сервиса; инструкция использует явный -f. git rm --cached исключает скиллы из проекта без удаления локальных инструкций; .agents/ игнорируется. OpenSpec artifacts и AGENTS.md остаются проектными правилами.

## Verification

Полная unit/func suite на выделенном PostgreSQL проверяет импорт и spawn workers. Ruff, lock, docs checker, strict MkDocs/OpenSpec; signed commit/push и actual six-job CI/Pages. Проверить отсутствие root files и tracked skills. Compose engine локально недоступен; содержимое сервиса сохраняется точно.
