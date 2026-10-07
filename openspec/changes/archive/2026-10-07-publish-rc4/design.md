## Context

GitHub wa-pis/iddqueue main/public, PyPI trusted publisher publish.yml/environmentpypi уже настроен. RC3 immutable assets находятся в dist/0.13.0rc3, их не перезаписывать.

## Decisions

Release gate в новой dist/0.13.0rc4; candidate signed commit после локальных проверок. Дождаться фактических six CI jobs. Signed v0.13.0rc4 указывает на candidate; GitHub prerelease wheel/sdist/checksums. Publish workflow скачивает exact candidate assets и проверяет SHA256 без rebuild. Проверить PyPI metadata/hashes и clean index installation/quickstart.

## Risks / Trade-offs

PyPI version immutable, неизвестный outcome требует readback, не слепого повторного upload. SQLAlchemy optional/sync; никаких DDL изменений RC3->RC4. Security review — статический standard scan с явно ограниченным prose/dependency coverage; не обещать отсутствие всех уязвимостей.

Candidatea529e5e CI5/6initialfailure выявил scan-plan lock reentrance. Включён fix-single-claim-lock-acquisition; RC4 ещё не published/tagged. Прежние локальные188pass/hashfacts сохраняются исторически, finalcandidate/hashes будут новыми.

Послеsingle-lockfix candidate6eb5aac CI5/6initialfailure встаромcrashoracle. Включёнfix-crash-test-message-correlation; runtimeassets unchanged, finalcandidateSHA будетновымпослеполнойпроверки.
