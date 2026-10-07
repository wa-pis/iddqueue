# Проверки — 2026-10-07

RC4preliminarycandidatea529e5e CI37555454492initial5/6: PG18/Python3.14 tests realfailure/retry и lockrelease failed; rerunfinal6/6 не маскирует баг. На dedicatedPG18.6(containerpostgres18,127.0.0.1:15434) forcedSeqScan при50других rows оставляет50реентрантных lock acquisitions послеодногоACK. EXPLAIN Filter вызывает pg_try передmessage_idfilter. Regression ACK/NACK доfix:2failed/23deselectedPG18(0.16s) иPG14(0.10s).

SQL uncorrelated scalar subquery одинраз наstatement; тотжепараметризованныйclaim/DBfilters, release одинраз. ПослеfixPG18 consumerconsistency/migration/failures38passed10.46s, включая missing/terminal hints и actual retryworker. Regression дополнительно assertsSeqScan (не только настройка planner). Fullgate/CI/новыеhashes pending.

Первый PG18 test setup вызвал SyntaxError из psqlmetacommand и test отсутствия witnessschema; не passing evidence. Послеудаления metacommand и создания witness schema checks executed успешно. FreshdisposablePG18; PG14 основной dedicatedcluster55433.

FinalPG18 EXPLAIN: InitPlan1/Result, One-Time Filter:(InitPlan1).col1 и SeqScan rowfilter без lockfunction; послеACK extra pg_advisory_unlock False. Полный scripts/check_release.sh exit0 наPG14.20/Python3.13.14:190passed58.58s; Ruff/lock/pipcheck/docsstrict/OpenSpec/build/LICENSE/base+monitoring+sqlalchemy installed/quickstart passed. Это новый gate, прежние188pass/hashcandidateисторические.

Signed6eb5aac pushmain. Isolated installedRC4wheel onPG18 additionally confirms forcedSeqScan/singleACKrelease, malformedNOTIFYsame sessions, SQLAlchemyatomicity and domainResults. Source/README/metadata bytes match assets. CI37556241736 pending.
