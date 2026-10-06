## 1. Optional adapter

- [ ] 1.1 Добавить минимальный helper и optional SQLAlchemy 2.x extra с reuse existing enqueue; проверить input/transaction/driver guards без core dependency.
- [ ] 1.2 Dedicated PG acceptance Connection/Session commit/rollback/NOTIFY, nested savepoint, delay/dedup, caller ownership и SQL error rollback; no separate broker pool transaction.
- [ ] 1.3 Документировать синхронный scope, explicit SQL/flush requirement, multi-bind explicit Connection и async limits; strict docs checks.
- [ ] 1.4 Полный unit/func, Ruff/lock/strict OpenSpec, build/LICENSE и base/extra installed wheel checks; signed commit/push и actual CI.
- [ ] 1.5 Evidence, main spec sync и archive после всех проверок.
