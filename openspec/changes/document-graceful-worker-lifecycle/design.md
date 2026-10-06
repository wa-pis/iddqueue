## Context

Dramatiq2.2.1 cli worker.stop(timeout=args.worker_shutdown_timeout), broker.close; default600000ms. Supervisor SIGHUP завершает subprocesses и exec restart, SIGTERM останавливает. Domain Dockerfile уже exec CMD.

## Goals / Non-Goals

Показать native lifecycle и достаточное ожидание container stop. Не обещать exactly-once/crash-safe side effects, не реализовывать custom orchestration.

## Decisions

Unix examples SIGTERM/SIGHUP supervisor PID, timeout120000ms и container grace150s как пример, пользователь рассчитывает по workload. Grace restart результат8tasks, новые PIDs; active3s job завершается послеSIGTERM. Конец сессий проверяется через pg_stat_activity. Для immutable Docker image обновление через replacement, SIGHUP перечитывает лишь доступный код.

## Risks / Trade-offs

SIGKILL/repeated signal/слишком короткий grace могут прервать actor. Shutdown timeout не обещает отмену arbitrary blocking I/O. Native Prometheus hard-restart stale state исправляется отдельным follow-up guidance, не graceful feature.
