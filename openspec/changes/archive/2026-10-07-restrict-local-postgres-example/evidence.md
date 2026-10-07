# Проверки — 2026-10-07

Исходный tracked mapping5432:5432 и postgres/passwordpostgres подтверждены security scan28044df (low CWE-1188, external exposure не установлена). Новый mapping127.0.0.1:5432:5432; `colima nerdctl -- compose -f examples/postgres/compose.yml config` exit0 возвращает host_ip127.0.0.1, target5432, published5432. Server не запускался: это проверка resolved config, не network penetration test.

Общий последовательный полный suite188passed61.47s, Ruff/lock/docs/OpenSpec passed. Подпись/CI/архив ожидаются.

Signedde9f077 pushmain: Tests37554835896 фактически6/6success, Documentation37554835914success.
