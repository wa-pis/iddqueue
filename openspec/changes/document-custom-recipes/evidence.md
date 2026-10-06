# Evidence

- Docs links и MkDocs strict build прошли; OpenSpec strict 20/20.
- Три Python блока извлечены прямо из guide и выполнены как myrecipe в temp directory: отдельный Dramatiq worker, producer result 5, worker exit 0.
- Dedicated PostgreSQL 14.20 localhost:55433, Python 3.13.14, development checkout; isolated temporary source directory. PG остановлен после проверки. Это не отдельная проверка установленного RC3.
- Runtime и packaging не менялись; full suite локально не повторялась. Удалённые CI результаты будут записаны после push.
