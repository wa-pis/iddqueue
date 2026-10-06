# Installed acceptance reproduction

Использовать только отдельный disposable PostgreSQL с запасом120connections, порт55433, userpostgres/databasepostgres. Fresh schema readiness_probe MUST отсутствовать. Собрать development wheel в /tmp/iddqueue-readiness-build; создать /tmp/iddqueue-readiness-venv, установить wheel[binary,monitoring,sqlalchemy]. run.py содержит assertion этого venv path. Запускать cwd этой директории, DATABASE_URL=postgresql://postgres@127.0.0.1:55433/postgres?application_name=readiness. PYTHONPATH должен отсутствовать.

```
/tmp/iddqueue-readiness-venv/bin/python run.py
```

После ~2min report записан /tmp/readiness-installed-soak.json; процесс ждёт SIGTERM для проверки exporter/Grafana. Ports9192storage,9193/9194native worker metrics. Завершить SIGTERM: stops worker processes, exporter, engine/pool, prints CONNECTIONS_AFTER_CLOSE, drops только созданную readiness_probe. До SIGTERM можно вызвать namespace PURGE явно для проверки retention; исходный run не выполняет purge автоматически. Требует schema отсутствии и фиксированные свободные ports. Не запускать на пользовательской базе.
