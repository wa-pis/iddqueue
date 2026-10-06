# Reproduction

Использовать setup из ../.. /verify-engineering-readiness/acceptance/README.md: dedicated PG55433 postgres, fresh readiness_probe отсутствует, установленный wheel в /tmp/iddqueue-readiness-venv, cwd этой директории, DATABASE_URL с application_name=readiness-grace. Запустить python grace.py, ports9197 свободны. SIGTERM shutdown выполняется автоматически. Script finally закрывает workers/broker и удаляет только свою schema. Never run against application data.
