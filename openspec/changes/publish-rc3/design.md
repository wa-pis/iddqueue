## Decisions

Повторить проверенный RC2 release flow: local dedicated PostgreSQL gate, signed candidate push и actual six-job CI. Собрать immutable assets с candidate commit, проверить LICENSE/installed acceptance, hashes; signed tag v0.13.0rc3 и GitHub prerelease. Затем fixed SHA/hash OIDC workflow, publication и PyPI hashes/clean index install. Исторические RC1/RC2 не изменять.

## Migration Plan

RC2 -> RC3 обновление пакета без DDL. Domain additive opt-in; existing dramatiq.actor сохраняется. Новые Domain actors требуют startup registration в каждом процессе, без hot rebind.

## Risks / Trade-offs

Нельзя публиковать rebuilt assets после release: проверять точные SHA256. PyPI version immutable; при ошибках не заменять файлы.
