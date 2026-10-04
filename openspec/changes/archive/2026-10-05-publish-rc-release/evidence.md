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

## Trusted Publishing setup

GitHub environment pypi создан. Workflow publish.yml распознан GitHub, ID 374855795. Manual main-only trigger; OIDC id-token:write; fixed SHA256 и candidate target для существующих assets; uv 0.11.23 --trusted-publishing always. YAML syntax (Psych), docs checker, strict OpenSpec 19/19: passed.
Commit be22062a43e1c44e357878f0bef9034ca8a4919f отправлен в main.
[Tests 37232019564](https://github.com/wa-pis/iddqueue/actions/runs/37232019564): completed/success, 6/6 (3.10/3.13/3.14 × PG14/18), полный release gate.
PyPI pending publisher должен добавить пользователь в аккаунте: iddqueue / wa-pis / iddqueue / publish.yml / pypi. Настройка PyPI ещё не подтверждена; publish workflow не запущен, upload не выполнен. Инструкция docs/publishing.md.

## PyPI publication — completed

Пользователь подтвердил pending publisher. Workflow [37232240070](https://github.com/wa-pis/iddqueue/actions/runs/37232240070) completed/success; [publish job](https://github.com/wa-pis/iddqueue/actions/runs/37232240070/job/111524232641). Workflow head a7fc6bf22ef3d0ead9f30d1a90fc97a771257445, package candidate по-прежнему 4e808632f920390100658b091bac2ab97a55eb2a.
PyPI JSON /pypi/iddqueue/0.13.0rc1/json подтвердил version и оба SHA256 точных файлов выше. Чистое /tmp/iddqueue-pypi-rc-install: uv pip install 'iddqueue[binary]==0.13.0rc1' exit 0; import вне checkout, SQL resource и metadata version 0.13.0rc1, CLI 0.13.0rc1. TestPyPI не использовался. Credentials не сохранялись.
Publication docs обновлены; исходные опубликованные artifacts не пересобирались/не заменялись.
