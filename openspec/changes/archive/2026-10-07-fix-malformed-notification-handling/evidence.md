# Проверки — 2026-10-07

Security scan c5721765-e9ab-4ff5-9555-79797457bc45, commit28044df: medium CWE-20 malformed NOTIFY, статический source trace; Daybreak not granted. До patch restricted-role regression: JSONDecodeError, 1failed/11deselected. После первого patch 34tests passed; независимое review выявило alternate durable UUID ACK lock mismatch. Исправлены общий lock key и in_processing identity, durable spelling сохранён. Final full188tests passed61.47s на Python3.13.14/PostgreSQL14.20(port55433), без параллельных тестов. Legit legacy/full/ID-only/scan и alternate durable IDs/ACK release проверены.

Ruff passed; uv lock --check passed с UV_CACHE_DIR=/tmp/iddqueue-uv-cache; strict docs build/check_docs passed; strict OpenSpec passed. Первое full выполнение186passed/1failed прервано пересекающимся отдельным pytest, чей session fixture TRUNCATE удалил pending shutdown task; это не passing evidence. Следующий полный запуск последовательно188passed. Отдельный focused запуск46passed/1failed из-за отсутствующего CLI в PATH, не засчитан полным проходом.

Runtime validation не подавляет connection/DB failures; invalid hints не логируются. Alternate UUID lock keys теперь canonical: не смешивать прежние workers при использовании custom noncanonical IDs. Обычные Dramatiq ID keys неизменны. CI/push и архив ещё ожидаются.

Signed190932d pushmain: Tests37553480914 success, Documentation37553480856 success. Проверка jobs выполнена отдельно; source review остаётся историческим audit28044df, remediation подтверждена regression/full suite.
