## GitHub

[Prerelase v0.13.0rc1](https://github.com/wa-pis/iddqueue/releases/tag/v0.13.0rc1) опубликован.
PUBLIC visibility, isPrerelease=true, targetCommitish=4e808632f920390100658b091bac2ab97a55eb2a.
Remote asset digests совпали:
- wheel 3acc297cfae2431f66bbf43393803489db9837ec888dc513dd87b8364ec1fb00;
- sdist a4688f1c7f79fef71ce78e1e151e7367fd0f96ee52e1010c3c3130f5ac07b5b1;
- SHA256SUMS d3608f349260d392fcd5b18a22e8bf5141e2e3dd687684bba018e2f572de7bf7.

## PyPI

`uv publish` точных wheel/sdist --trusted-publishing never: exit 2,
`Missing credentials for https://upload.pypi.org/legacy/`.
Публикация не выполнена; credential env отсутствуют, .pypirc отсутствует (содержимое secrets не запрашивалось/не выводилось).
Пользователь сообщил о наличии PyPI account; требуется настройка authentication.
