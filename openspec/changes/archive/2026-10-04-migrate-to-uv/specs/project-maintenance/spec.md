## ADDED Requirements

### Requirement: Locked uv verification environment

Проект SHALL использовать version-controlled uv.lock для development и CI. Обязательные проверки SHALL отклонять рассогласование metadata/lock без автоматического изменения lock. Base и monitoring wheel acceptance, LICENSE/SQL resources и полная Python/PostgreSQL матрица MUST сохраняться.

#### Scenario: Stale lockfile
- **WHEN** dependency metadata изменена без обновления uv.lock
- **THEN** locked sync или lock check завершается ошибкой до успешного CI/release gate

#### Scenario: Installed wheel acceptance
- **WHEN** uv собирает wheel и sdist
- **THEN** установленный вне checkout wheel поддерживает import/CLI и все SQL resources, LICENSE сохранён в обоих форматах, base/monitoring проверены отдельно

#### Scenario: Contributor setup
- **WHEN** contributor выполняет документированные uv sync и release checks на выделенном PostgreSQL
- **THEN** установлен dev group и нужные extras; тесты, docs и сборка выполняются без Poetry
