# Evidence

- Docs links и MkDocs strict build прошли; OpenSpec strict 20/20.
- Три Python блока извлечены прямо из guide и выполнены как myrecipe в temp directory: отдельный Dramatiq worker, producer result 5, worker exit 0.
- Dedicated PostgreSQL 14.20 localhost:55433, Python 3.13.14, development checkout; isolated temporary source directory. PG остановлен после проверки. Это не отдельная проверка установленного RC3.
- Runtime и packaging не менялись; full suite локально не повторялась. Удалённые CI результаты будут записаны после push.

- Signed commit 0d13b7cd76a4b47fc56c8c08747bd064a441ce84, signature G, push main. Documentation 37543145134 success (deployed). Tests 37543145122 final 6/6 success: first attempt Python3.13/PG14 failed existing test_retry timeout8s and test_delay elapsed0.018636>1 assertion; failed-job rerun unchanged commit passed. Runtime/tests not changed; instability not fixed by this documentation change.
