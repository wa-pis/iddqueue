## Verification

Проверено локально 2026-10-02.

- LICENSE побайтно совпадает с upstream commit
  80b1a490d0a494925a9f8be399a11b38cee5480a; сохранены copyright DALIBO
  и полный текст. SHA256 закреплён в scripts/check_license.py.
- poetry check/build: успешно; wheel и sdist версии 0.13.0 собраны.
- scripts/check_license.py подтвердил полный LICENSE в обоих артефактах
  и PostgreSQL в License-Expression (также поддерживается старый License).
- Отрицательные проверки временных wheels: отсутствие LICENSE и изменённый
  текст оба приводят к ValueError; исходные артефакты не менялись.
- README содержит attribution исходного проекта и условия распространения,
  не заменяя credits и не обещая отсутствия любых претензий.
- Ruff успешно. Strict OpenSpec validation успешно.
- CI дополнен сборкой и проверкой артефактов; удалённый запуск не выполнялся.

## Limits

Runtime и SQL не менялись: PostgreSQL suite не повторялась. Предыдущие 64
теста остаются результатом последнего runtime-прогона. Публикации нет;
GitHub identity ожидает пользователя. Лицензии зависимостей не изменены.
